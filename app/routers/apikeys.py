"""
API Key 管理路由

路径前缀: /api/v1/apikeys
提供 API Key 的创建、列表、撤销功能。
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import delete_cache
from app.core.database import get_db
from app.core.security import hash_api_key
from app.models.api_key import APIKey
from app.models import User

router = APIRouter(prefix="/api/v1/apikeys", tags=["API Keys"])


# ——— Schemas ————————————————————————————————————————————————————————————

class APIKeyResponse(BaseModel):
    """创建 API Key 成功后的响应（包含明文 key，只显示一次）"""
    id: str
    key: str  # 明文（仅在此响应中显示）
    key_prefix: str
    name: Optional[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class APIKeyBrief(BaseModel):
    """API Key 列表项（不包含明文）"""
    id: str
    key_prefix: str
    name: Optional[str]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


# ——— 辅助函数 ————————————————————————————————————————————————————————————

async def get_current_user_id(db: AsyncSession, token: str) -> Optional[str]:
    """从 Authorization: Bearer token 中提取 user_id"""
    from app.core.security import decode_access_token, is_token_blacklisted
    payload = decode_access_token(token)
    if not payload:
        return None
    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti):
        return None
    return payload.get("sub")


async def require_auth(
    authorization: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> str:
    """
    验证 Bearer Token，返回 user_id。
    简化版依赖（复用 auth 路由逻辑）。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[7:]  # 去掉 "Bearer " 前缀
    user_id = await get_current_user_id(db, token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户存在且启用
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户不存在或已被禁用",
        )
    return user_id


# ——— 路由 ————————————————————————————————————————————————————————————

@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    name: Optional[str] = None,
    expires_days: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = None,
):
    """
    创建新的 API Key

    Path: POST /api/v1/apikeys/
    Query:
        - name: 密钥名称（可选）
        - expires_days: 有效期天数（可选，None=永不过期）

    返回明文 API Key（只在此接口显示一次，请妥善保存）。
    """
    user_id = await require_auth(authorization, db)

    # 生成 key
    raw_key = f"sk-{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:12]  # sk-xxx... 显示前缀

    # 计算过期时间
    expires_at: Optional[datetime] = None
    if expires_days is not None and expires_days > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

    # 写入数据库
    api_key = APIKey(
        user_id=user_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        is_active=True,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return APIKeyResponse(
        id=api_key.id,
        key=raw_key,  # 只在此处显示明文
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
    )


@router.get("/", response_model=list[APIKeyBrief])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = None,
):
    """
    列出当前用户的所有 API Key

    Path: GET /api/v1/apikeys/
    """
    user_id = await require_auth(authorization, db)

    stmt = (
        select(APIKey)
        .where(APIKey.user_id == user_id)
        .order_by(APIKey.created_at.desc())
    )
    result = await db.execute(stmt)
    keys = result.scalars().all()

    return [
        APIKeyBrief(
            id=k.id,
            key_prefix=k.key_prefix,
            name=k.name,
            is_active=k.is_active,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            expires_at=k.expires_at,
        )
        for k in keys
    ]


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = None,
):
    """
    撤销（删除）指定的 API Key

    Path: DELETE /api/v1/apikeys/{key_id}
    """
    user_id = await require_auth(authorization, db)

    # 验证 key 属于当前用户
    stmt = select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在或无权访问",
        )

    # 删除缓存
    delete_cache(f"apikey:{api_key.key_hash}")

    # 删除记录
    await db.delete(api_key)
    await db.commit()

    return {"message": "API Key 已撤销"}
