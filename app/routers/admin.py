"""
管理后台 API - 包含限流统计和数据库连接池状态

注意：这些端点默认不暴露在公网，生产环境应通过内部网络或 VPN 访问。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.rate_limit import limiter

router = APIRouter(prefix="/admin", tags=["Admin"])


class RateLimitStats(BaseModel):
    total_requests: int
    enabled: bool
    message: str


@router.get("/rate-limits/stats", response_model=RateLimitStats)
async def get_rate_limit_stats():
    """
    获取限流统计信息

    返回限流功能的启用状态和基本统计。
    注意：详细统计（如每个 IP 的请求数）需要接入持久化存储。
    """
    try:
        # limiter.stats() 返回限流器统计字典
        stats = limiter.stats()
        return RateLimitStats(
            total_requests=stats.get("total_requests", 0),
            enabled=True,
            message="限流已启用"
        )
    except Exception as e:
        # 如果统计不可用，返回基本信息
        return RateLimitStats(
            total_requests=0,
            enabled=True,
            message=f"限流已启用（统计详情: {str(e)}）"
        )


class PoolStatus(BaseModel):
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    invalid: int | None
    is_sqlite: bool


@router.get("/db/pool-status", response_model=PoolStatus)
async def pool_status():
    """
    数据库连接池状态

    返回当前数据库连接池的使用情况：
    - pool_size: 连接池大小
    - checked_in: 空闲连接数
    - checked_out: 已借出连接数
    - overflow: 溢出连接数（超过 pool_size 的连接）
    - invalid: 无效连接数
    """
    from app.core.database import engine, _is_sqlite

    if _is_sqlite:
        # SQLite 没有连接池概念
        return PoolStatus(
            pool_size=0,
            checked_in=0,
            checked_out=0,
            overflow=0,
            invalid=None,
            is_sqlite=True
        )

    pool = engine.pool
    return PoolStatus(
        pool_size=pool.size(),
        checked_in=pool.checkedin(),
        checked_out=pool.checkedout(),
        overflow=pool.overflow(),
        invalid=pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else None,
        is_sqlite=False
    )


class CeleryStatus(BaseModel):
    celery_available: bool
    redis_available: bool
    message: str


@router.get("/celery/status", response_model=CeleryStatus)
async def celery_status():
    """
    Celery/Redis 状态检查

    返回 Celery 和 Redis 的可用性状态。
    """
    from app.tasks.celery_app import is_celery_available

    celery_ok = is_celery_available()
    return CeleryStatus(
        celery_available=celery_ok,
        redis_available=celery_ok,
        message="Celery/Redis 正常" if celery_ok else "Celery/Redis 不可用，将使用同步执行"
    )
