"""
Celery Tasks Module

提供异步任务处理能力，支持：
- Celery 异步执行（Redis broker）
- 优雅降级到同步执行（Celery 不可用时）
"""

from app.tasks.celery_app import celery
from app.tasks.task_handlers import send_email_task, execute_task

__all__ = ["celery", "send_email_task", "execute_task"]
