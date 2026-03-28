"""
Celery 配置

配置 Celery 使用 Redis 作为 broker 和 backend。
如果 Redis 不可用，celery_app.check_availability() 返回 False，
上游应降级为同步执行。
"""

import logging

from celery import Celery, signals

logger = logging.getLogger(__name__)

celery = Celery(
    "deepagents",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@signals.worker_ready.connect
def on_worker_ready(**kwargs):
    logger.info("Celery worker is ready")


@signals.worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    logger.info("Celery worker is shutting down")


def is_celery_available() -> bool:
    """
    检查 Celery/Redis 是否可用。
    用于优雅降级判断。
    """
    try:
        from app.core.config import settings
        import redis

        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            socket_connect_timeout=2,
        )
        r.ping()
        return True
    except Exception as e:
        logger.warning("Celery/Redis not available, will use synchronous execution: %s", e)
        return False
