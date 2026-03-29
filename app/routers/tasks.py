"""
任务队列路由

路径前缀: /api/v1/tasks（由 main.py 控制版本前缀）
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.email import notify_task_status_change
from app.core.webhook import notify_task_webhook
from app.models import Task, TaskStatus, TaskPriority, User
from app.schemas import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse
from app.tasks.celery_app import celery, is_celery_available
from app.tasks.task_handlers import send_email_task, execute_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ——— Create ————————————————————————————————————————————————————————————————

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """创建新任务"""
    # 验证 owner 存在
    stmt = select(User).where(User.id == task_in.owner_id)
    result = await db.execute(stmt)
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="所属用户不存在")

    task = Task(
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority,
        tags=task_in.tags or [],
        max_retries=task_in.max_retries,
        owner_id=task_in.owner_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 触发 webhook（创建事件）
    await notify_task_webhook(
        event_type="task.created",
        task_id=task.id,
        task_title=task.title,
        status=task.status.value,
        owner_id=task.owner_id,
        background_tasks=background_tasks,
    )

    return task


# ——— Dispatch（Celery 异步 / 同步降级）—————————————————————————————————

@router.post("/{task_id}/dispatch", response_model=dict)
async def dispatch_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    将任务分发给 Celery worker 异步执行。
    
    如果 Celery/Redis 不可用，则降级为同步执行。
    仅允许 pending 状态的任务被分发。
    """
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"任务状态为 {task.status.value}，仅 pending 任务可分发")

    if is_celery_available():
        # 异步：交给 Celery worker 执行
        execute_task.delay(task_id, task.owner_id, task.title)
        return {
            "mode": "async",
            "task_id": task_id,
            "message": "任务已提交到 Celery 队列",
        }
    else:
        # 降级：同步执行（阻塞）
        from datetime import datetime
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        await db.commit()

        try:
            import time
            time.sleep(1)  # 模拟执行
            task.status = TaskStatus.SUCCESS
            task.result = f"Task '{task.title}' completed (sync mode)"
            task.completed_at = datetime.utcnow()
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
        finally:
            await db.commit()
            await db.refresh(task)

        return {
            "mode": "sync",
            "task_id": task_id,
            "status": task.status.value,
            "message": "Celery 不可用，任务已同步执行",
        }


# ——— Read（分页 + 搜索 + 过滤）————————————————————————————————————

@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    status_filter: Optional[TaskStatus] = Query(None, alias="status", description="按状态过滤"),
    owner_id: Optional[str] = Query(None, description="按用户 ID 过滤"),
    search: Optional[str] = Query(None, description="搜索任务标题/描述"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询任务列表

    支持按 status、owner_id 过滤，支持搜索标题/描述
    """
    skip = (page - 1) * page_size

    stmt = select(Task)

    if status_filter is not None:
        stmt = stmt.where(Task.status == status_filter)
    if owner_id is not None:
        stmt = stmt.where(Task.owner_id == owner_id)
    if search:
        stmt = stmt.where(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
            )
        )

    stmt = stmt.order_by(Task.created_at.desc()).offset(skip).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """根据 ID 获取单个任务"""
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


# ——— Update Status（核心操作 + webhook + email） ————————————————————

@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    status_in: TaskStatusUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    更新任务状态（任务执行器调用）

    状态流转: pending → running → success / failed / cancelled
    同时更新 started_at / completed_at 时间戳
    触发 Webhook 和邮件通知
    """
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    old_status = task.status.value
    task.status = status_in.status

    # 设置时间戳
    if status_in.status == TaskStatus.RUNNING and task.started_at is None:
        task.started_at = datetime.utcnow()
    elif status_in.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED):
        task.completed_at = datetime.utcnow()

    # 填入结果或错误信息
    if status_in.result is not None:
        task.result = status_in.result
    if status_in.error is not None:
        task.error = status_in.error
    if status_in.progress is not None:
        task.progress = status_in.progress

    await db.commit()
    await db.refresh(task)

    # 触发 Webhook
    await notify_task_webhook(
        event_type="task.status_changed",
        task_id=task.id,
        task_title=task.title,
        status=task.status.value,
        result=task.result,
        error=task.error,
        owner_id=task.owner_id,
        background_tasks=background_tasks,
    )

    # 触发邮件通知（任务完成/失败）
    if old_status != status_in.status.value and status_in.status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
        stmt = select(User).where(User.id == task.owner_id)
        result = await db.execute(stmt)
        owner = result.scalar_one_or_none()
        if owner:
            await notify_task_status_change(
                task_title=task.title,
                task_id=task.id,
                old_status=old_status,
                new_status=status_in.status.value,
                user_email=owner.email,
                background_tasks=background_tasks,
            )

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新任务信息（部分更新）"""
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 不允许在非 pending 状态时修改部分字段（可按需调整）
    if task.status != TaskStatus.PENDING:
        update_data = task_in.model_dump(exclude_unset=True)
        for field in ("title", "description", "priority", "max_retries", "tags"):
            if field in update_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"任务已开始，不允许修改 {field}",
                )
    else:
        update_data = task_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task


# ——— Retry ————————————————————————————————————————————————————————————————

@router.patch("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """重试失败任务
    
    PATCH /api/v1/tasks/{id}/retry
    将任务重置为 pending，重试计数 +1
    """
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.FAILED:
        raise HTTPException(status_code=400, detail="只有失败任务可以重试")

    if task.retry_count >= task.max_retries:
        raise HTTPException(status_code=400, detail="已达到最大重试次数")

    old_status = task.status.value
    task.status = TaskStatus.PENDING
    task.retry_count += 1
    task.error = None
    task.started_at = None
    task.completed_at = None
    task.progress = 0

    await db.commit()
    await db.refresh(task)

    # 触发 webhook
    await notify_task_webhook(
        event_type="task.retried",
        task_id=task.id,
        task_title=task.title,
        status=task.status.value,
        owner_id=task.owner_id,
        background_tasks=background_tasks,
    )

    return task


# ——— Delete / Cancel ————————————————————————————————————————————————

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """删除任务（如果正在运行会失败）"""
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail="任务正在运行，无法删除")

    await db.delete(task)
    await db.commit()


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """取消任务（仅 pending 或 running 状态可取消）"""
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
        raise HTTPException(status_code=400, detail=f"当前状态 {task.status.value} 无法取消")

    task.status = TaskStatus.CANCELLED
    task.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)

    # 触发 webhook
    await notify_task_webhook(
        event_type="task.cancelled",
        task_id=task.id,
        task_title=task.title,
        status=task.status.value,
        owner_id=task.owner_id,
        background_tasks=background_tasks,
    )

    return task
