"""
Flower 监控配置

Flower 是 Celery 的官方监控工具，提供实时 Web UI：
- Worker 状态监控
- 任务列表和历史
- 任务详情和重试
- 资源使用情况

访问地址: http://localhost:5555 (开发) 或 http://your-domain/flower (生产)
"""

# Flower 监控配置
FLOWER_URL = "/flower"
FLOWER_PORT = 5555
FLOWER_BASIC_AUTH = "flower:flower"  # 简单认证，生产环境应使用更复杂的认证

# Flower Celery 配置
FLOWER_CELERY_BROKER = "redis://redis:6379/0"
FLOWER_CELERY_RESULT_BACKEND = "redis://redis:6379/0"
