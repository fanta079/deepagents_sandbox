"""
Celery Beat 配置 - 支持定时任务
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "cleanup-expired-tasks": {
        "task": "app.tasks.celery_app.cleanup_expired_tasks",
        "schedule": crontab(minute=0, hour="*/1"),  # 每小时执行
    },
    "health-check-all-workers": {
        "task": "app.tasks.celery_app.health_check",
        "schedule": 300.0,  # 5分钟
    },
}
