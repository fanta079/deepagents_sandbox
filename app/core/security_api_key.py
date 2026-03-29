"""
API Key 认证依赖

提供 FastAPI Depends 依赖项，用于验证 X-API-Key 请求头。
支持缓存加速验证，避免每次请求都查询数据库。
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache, set_cache
from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_api_key
from app.models.api_key import APIKey

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# 缓存 TTL（秒）
_API_KEY_CACHE_TTL = 300  # 5 分钟


async def get_api_key_auth(
    api_key: Optional[str] = Depends(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    """
    FastAPI 依赖：验证 X-API-Key 请求头

    验证流程：
    1. 检查 header 是否存在
    2. 计算 key_hash，尝试从缓存获取
    3. 缓存未命中则查询数据库
    4. 检查 key 是否激活、是否过期
    5. 更新 last_used_at（异步，不阻塞响应）

    Args:
        api_key: X-API-Key header 值
        db: 数据库会话

    Returns:
        验证通过的 APIKey 模型实例

    Raises:
        HTTPException: 401 Unauthorized — 缺少或无效的 API Key
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 非 API Key 认证模式时直接跳过（方便开发）
    if not getattr(settings, "API_KEY_ENABLED", True):
        return None  # type: ignore[return-value]

    # 计算哈希
    key_hash = hash_api_key(api_key)
    cache_key = f"apikey:{key_hash}"

    # 1) 缓存命中
    cached = get_cache(cache_key)
    if cached:
        try:
            cached_data = json.loads(cached)
            # 检查是否过期（缓存层）
            if cached_data.get("expires_at"):
                expires = datetime.fromisoformat(cached_data["expires_at"])
                if expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                    # 已过期，删除缓存并拒绝
                    from app.core.cache import delete_cache
                    delete_cache(cache_key)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="API Key 已过期",
                    )
            return cached_data
        except (json.JSONDecodeError, TypeError):
            # 缓存数据损坏，当成未命中处理
            pass

    # 2) 数据库查询
    stmt = select(APIKey).where(APIKey.key_hash == key_hash)
    result = await db.execute(stmt)
    api_key_obj: Optional[APIKey] = result.scalar_one_or_none()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 3) 检查激活状态
    if not api_key_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key 已停用",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 4) 检查过期时间
    if api_key_obj.expires_at:
        if api_key_obj.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key 已过期",
                headers={"WWW-Authenticate": "ApiKey"},
            )

    # 5) 写入缓存
    cache_data = {
        "id": api_key_obj.id,
        "user_id": api_key_obj.user_id,
        "key_prefix": api_key_obj.key_prefix,
        "name": api_key_obj.name,
        "expires_at": api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
    }
    set_cache(cache_key, json.dumps(cache_data), expire_seconds=_API_KEY_CACHE_TTL)

    # 6) 异步更新 last_used_at（不阻塞响应）
    import asyncio
    from app.core.database import AsyncSessionLocal

    async def _update_last_used():
        async with AsyncSessionLocal() as session:
            s = select(APIKey).where(APIKey.id == api_key_obj.id)
            r = await session.execute(s)
            obj: Optional[APIKey] = r.scalar_one_or_none()
            if obj:
                obj.last_used_at = datetime.utcnow()
                await session.commit()

    try:
        asyncio.create_task(_update_last_used())
    except Exception:
        pass  # 不阻塞主请求

    return api_key_obj
