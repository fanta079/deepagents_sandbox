"""
Celery 任务处理函数

注意：这些任务函数运行在 Celery worker 进程中。
避免在此模块中直接使用 FastAPI 依赖注入的数据库会话，
如有需要请在任务内部创建新的会话。
"""

import asyncio
import logging
import time
from typing import Optional

from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(bind=True, name="tasks.send_email")
def send_email_task(self, to: str, subject: str, body: str) -> dict:
    """
    异步发送邮件任务（Celery worker 执行）

    Args:
        to: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文

    Returns:
        {"status": "sent"|"failed", "to": str, "error"?: str}
    """
    from app.core.email import send_email_sync

    try:
        success = send_email_sync(to_email=to, subject=subject, body=body)
        if success:
            logger.info("Email sent via Celery: %s", to)
            return {"status": "sent", "to": to}
        else:
            logger.warning("Email send returned False: %s", to)
            return {"status": "failed", "to": to, "error": "SMTP send returned False"}
    except Exception as e:
        logger.error("Email task failed for %s: %s", to, e)
        return {"status": "failed", "to": to, "error": str(e)}


@celery.task(bind=True, name="tasks.execute_task")
def execute_task(self, task_id: str, owner_id: str, task_title: str) -> dict:
    """
    异步任务执行入口（Celery worker 执行）

    实际业务逻辑可在此扩展，如调用沙箱后端、Agent 等。

    Args:
        task_id: 任务 ID
        owner_id: 所属用户 ID
        task_title: 任务标题（用于日志）

    Returns:
        {"status": "success"|"failed", "task_id": str, "result"?: str, "error"?: str}
    """
    from datetime import datetime

    logger.info("Celery executing task: %s (id=%s)", task_title, task_id)

    async def _update_status(
        status, result: Optional[str] = None, error: Optional[str] = None
    ):
        from app.core.database import AsyncSessionLocal
        from app.models.task import TaskStatus
        from sqlalchemy import select
        from app.models.task import Task as TaskModel

        async with AsyncSessionLocal() as db:
            stmt = select(TaskModel).where(TaskModel.id == task_id)
            result_row = await db.execute(stmt)
            task = result_row.scalar_one_or_none()
            if task:
                task.status = status
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
                if status == TaskStatus.RUNNING and task.started_at is None:
                    task.started_at = datetime.utcnow()
                elif status in (
                    TaskStatus.SUCCESS,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                ):
                    task.completed_at = datetime.utcnow()
                await db.commit()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(_update_status(
            __import__("app.models.task", fromlist=["TaskStatus"]).TaskStatus.RUNNING
        ))

        # 模拟任务执行（替换为实际沙箱/Agent 调用）
        time.sleep(2)

        TaskStatus = __import__("app.models.task", fromlist=["TaskStatus"]).TaskStatus
        loop.run_until_complete(
            _update_status(
                TaskStatus.SUCCESS,
                result=f"Task '{task_title}' completed successfully",
            )
        )
        logger.info("Task completed: %s", task_id)
        return {"status": "success", "task_id": task_id}

    except Exception as e:
        logger.error("Task failed: %s, error: %s", task_id, e)
        try:
            TaskStatus = __import__("app.models.task", fromlist=["TaskStatus"]).TaskStatus
            loop.run_until_complete(
                _update_status(TaskStatus.FAILED, error=str(e))
            )
        except Exception:
            pass
        return {"status": "failed", "task_id": task_id, "error": str(e)}
    finally:
        loop.close()
