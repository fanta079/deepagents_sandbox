"""
认证路由 — JWT 登录

路径前缀: /api/v1/auth
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    decode_access_token,
)
from app.core.exceptions import UnauthorizedException
from app.core.cache import blacklist_token
from app.models import User
from app.schemas import TokenResponse, Token, RefreshRequest, LoginRequest, LogoutRequest

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(login_in: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    用户登录，获取 JWT Access Token 和 Refresh Token

    Path: POST /api/v1/auth/login
    Access Token 有效期: 30 分钟
    Refresh Token 有效期: 7 天
    """
    stmt = select(User).where(User.username == login_in.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_in: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    使用 Refresh Token 换取新的 Access Token

    Path: POST /api/v1/auth/refresh
    Refresh Token 有效期: 7 天
    """
    payload = verify_refresh_token(refresh_in.refresh_token)
    if not payload:
        raise UnauthorizedException(message="Refresh Token 无效或已过期")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(message="Refresh Token 解析失败")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedException(message="用户不存在或已被禁用")

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(
    logout_in: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登出，将当前 Access Token 加入黑名单

    Path: POST /api/v1/auth/logout
    """
    payload = decode_access_token(logout_in.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    if jti:
        # 黑名单有效期最多 1 天，与 access_token 最大生命周期对齐
        blacklist_token(jti, expire_seconds=60 * 60 * 24)

    return {"message": "登出成功"}
