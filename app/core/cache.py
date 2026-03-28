"""
缓存层 — Redis（优先）或内存回退

提供统一的 get_cache / set_cache / delete_cache 接口，
并封装 token 黑名单操作。
"""

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# ——— 存储后端选择 —————————————————————————————————————————————

_redis_client: Optional[object] = None
_use_redis = False

try:
    import redis

    _redis_client = redis.Redis(
        host=settings.REDIS_HOST if hasattr(settings, "REDIS_HOST") else "localhost",
        port=settings.REDIS_PORT if hasattr(settings, "REDIS_PORT") else 6379,
        db=settings.REDIS_DB if hasattr(settings, "REDIS_DB") else 0,
        password=settings.REDIS_PASSWORD if hasattr(settings, "REDIS_PASSWORD") else None,
        decode_responses=True,
        socket_connect_timeout=2,
    )
    _redis_client.ping()
    _use_redis = True
    logger.info("✅ Redis 连接成功，使用 Redis 作为缓存后端")
except Exception:
    _use_redis = False
    logger.warning("⚠️ Redis 不可用，回退到内存缓存（进程重启后失效）")

# ——— 内存回退存储 ————————————————————————————————————————————

_memory_store: dict[str, tuple[str, Optional[float]]] = {}
"""内存缓存: { key: (value, expire_timestamp_or_None) }"""


def _mem_cleanup() -> None:
    """清理已过期的内存缓存项"""
    import time
    now = time.time()
    expired = [k for k, (_, exp) in _memory_store.items() if exp is not None and exp <= now]
    for k in expired:
        del _memory_store[k]


# ——— 公开接口 ————————————————————————————————————————————————

def get_cache(key: str) -> Optional[str]:
    """
    获取缓存值。

    Args:
        key: 缓存键

    Returns:
        缓存值，不存在或已过期返回 None
    """
    if _use_redis:
        return _redis_client.get(key)  # type: ignore[return-value]

    # 内存回退
    _mem_cleanup()
    entry = _memory_store.get(key)
    if entry is None:
        return None
    value, expire = entry
    if expire is not None:
        import time
        if expire <= time.time():
            del _memory_store[key]
            return None
    return value


def set_cache(key: str, value: str, expire_seconds: Optional[int] = None) -> None:
    """
    设置缓存值。

    Args:
        key: 缓存键
        value: 缓存值
        expire_seconds: TTL 秒数，None 表示永不过期
    """
    if _use_redis:
        if expire_seconds:
            _redis_client.setex(key, expire_seconds, value)  # type: ignore[attr-defined]
        else:
            _redis_client.set(key, value)  # type: ignore[attr-defined]
        return

    # 内存回退
    import time
    expire_ts: Optional[float] = None
    if expire_seconds is not None:
        expire_ts = time.time() + expire_seconds
    _memory_store[key] = (value, expire_ts)


def delete_cache(key: str) -> None:
    """
    删除缓存项。

    Args:
        key: 缓存键
    """
    if _use_redis:
        _redis_client.delete(key)  # type: ignore[attr-defined]
        return

    # 内存回退
    _memory_store.pop(key, None)


# ——— Token 黑名单 —————————————————————————————————————————————

TOKEN_BLACKLIST_PREFIX = "token:blacklist:"
"""Redis key 前缀"""


def blacklist_token(jti: str, expire_seconds: int = 86400) -> None:
    """
    将 token JTI 加入黑名单（logout 时调用）。

    Args:
        jti: JWT Token ID（JWT payload 中的 jti 字段）
        expire_seconds: 黑名单有效期，默认 1 天（与 access_token 最大生命周期对齐）
    """
    key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"
    set_cache(key, "1", expire_seconds=expire_seconds)


def is_token_blacklisted(jti: str) -> bool:
    """
    检查 token JTI 是否在黑名单中。

    Args:
        jti: JWT Token ID

    Returns:
        True = 在黑名单（已 logout），False = 正常
    """
    key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"
    return get_cache(key) is not None
