"""
任务队列路由 v2 — 批量操作 + 批量分发

路径前缀: /api/v2/tasks（由 main.py 控制版本前缀）
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel
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


# ——— Schemas ————————————————————————————————————————————————————————————————

class TaskBatchCreate(BaseModel):
    """批量创建任务"""
    tasks: List[TaskCreate]


class TaskBatchDispatch(BaseModel):
    """批量分发任务"""
    task_ids: List[str]


# ——— Create ————————————————————————————————————————————————————————————————

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task_v2(
    task_in: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """创建新任务"""
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

    await notify_task_webhook(
        event_type="task.created",
        task_id=task.id,
        task_title=task.title,
        status=task.status.value,
        owner_id=task.owner_id,
        background_tasks=background_tasks,
    )

    return task


# ——— Batch Create ————————————————————————————————————————————————————

@router.post("/batch", response_model=List[TaskResponse], status_code=status.HTTP_201_CREATED)
async def batch_create_tasks(
    request: TaskBatchCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """批量创建任务"""
    # 验证所有 owner_id 存在
    owner_ids = list({t.owner_id for t in request.tasks})
    stmt = select(User.id).where(User.id.in_(owner_ids))
    result = await db.execute(stmt)
    existing_owners = set(row[0] for row in result.fetchall())

    missing = [uid for uid in owner_ids if uid not in existing_owners]
    if missing:
        raise HTTPException(status_code=404, detail=f"所属用户不存在: {missing}")

    tasks = []
    for task_in in request.tasks:
        task = Task(
            title=task_in.title,
            description=task_in.description,
            priority=task_in.priority,
            tags=task_in.tags or [],
            max_retries=task_in.max_retries,
            owner_id=task_in.owner_id,
        )
        db.add(task)
        tasks.append(task)

    await db.commit()

    for task in tasks:
        await db.refresh(task)

    return tasks


# ——— Dispatch（Celery 异步 / 同步降级）—————————————————————————————————

@router.post("/{task_id}/dispatch", response_model=dict)
async def dispatch_task_v2(
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
        execute_task.delay(task_id, task.owner_id, task.title)
        return {
            "mode": "async",
            "task_id": task_id,
            "message": "任务已提交到 Celery 队列",
        }
    else:
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        await db.commit()

        try:
            import time
            time.sleep(1)
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


# ——— Batch Dispatch ——————————————————————————————————————————————————

@router.post("/batch/dispatch", response_model=dict)
async def batch_dispatch_tasks(
    request: TaskBatchDispatch,
    db: AsyncSession = Depends(get_db),
):
    """批量分发任务"""
    stmt = select(Task).where(Task.id.in_(request.task_ids))
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    if len(tasks) != len(request.task_ids):
        found_ids = {t.id for t in tasks}
        missing = [tid for tid in request.task_ids if tid not in found_ids]
        raise HTTPException(status_code=404, detail=f"任务不存在: {missing}")

    dispatched = []
    skipped = []

    for task in tasks:
        if task.status == TaskStatus.PENDING:
            if is_celery_available():
                execute_task.delay(task.id, task.owner_id, task.title)
            else:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.utcnow()
            dispatched.append(task.id)
        else:
            skipped.append({"task_id": task.id, "status": task.status.value})

    await db.commit()

    return {
        "dispatched": dispatched,
        "skipped": skipped,
        "mode": "async" if is_celery_available() else "sync",
    }


# ——— Read（分页 + 搜索 + 过滤）————————————————————————————————————

@router.get("/", response_model=list[TaskResponse])
async def list_tasks_v2(
    status_filter: Optional[TaskStatus] = Query(None, alias="status", description="按状态过滤"),
    owner_id: Optional[str] = Query(None, description="按用户 ID 过滤"),
    search: Optional[str] = Query(None, description="搜索任务标题/描述"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    db: AsyncSession = Depends(get_db),
):
    """查询任务列表"""
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
async def get_task_v2(task_id: str, db: AsyncSession = Depends(get_db)):
    """根据 ID 获取单个任务"""
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


# ——— Update Status ————————————————————————————————————————————————————

@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status_v2(
    task_id: str,
    status_in: TaskStatusUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """更新任务状态"""
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    old_status = task.status.value
    task.status = status_in.status

    if status_in.status == TaskStatus.RUNNING and task.started_at is None:
        task.started_at = datetime.utcnow()
    elif status_in.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED):
        task.completed_at = datetime.utcnow()

    if status_in.result is not None:
        task.result = status_in.result
    if status_in.error is not None:
        task.error = status_in.error
    if status_in.progress is not None:
        task.progress = status_in.progress

    await db.commit()
    await db.refresh(task)

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
async def update_task_v2(
    task_id: str,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新任务信息"""
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

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
async def retry_task_v2(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """重试失败任务"""
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.FAILED:
        raise HTTPException(status_code=400, detail="只有失败任务可以重试")

    if task.retry_count >= task.max_retries:
        raise HTTPException(status_code=400, detail="已达到最大重试次数")

    task.status = TaskStatus.PENDING
    task.retry_count += 1
    task.error = None
    task.started_at = None
    task.completed_at = None
    task.progress = 0

    await db.commit()
    await db.refresh(task)

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
async def delete_task_v2(task_id: str, db: AsyncSession = Depends(get_db)):
    """删除任务"""
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
async def cancel_task_v2(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """取消任务"""
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

    await notify_task_webhook(
        event_type="task.cancelled",
        task_id=task.id,
        task_title=task.title,
        status=task.status.value,
        owner_id=task.owner_id,
        background_tasks=background_tasks,
    )

    return task
