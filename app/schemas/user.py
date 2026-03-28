"""
User Pydantic Schemas — 请求/响应模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ——— Base ————————————————————————————————————————————————————————————————

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")


# ——— Create ————————————————————————————————————————————————————————————————

class UserCreate(UserBase):
    """创建用户时的请求体"""
    password: str = Field(..., min_length=6, max_length=128, description="密码")


# ——— Update ————————————————————————————————————————————————————————————————

class UserUpdate(BaseModel):
    """更新用户时的请求体（全字段可选）"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    is_active: Optional[bool] = None


# ——— Response ————————————————————————————————————————————————————————————————

class UserResponse(UserBase):
    """用户响应模型（不包含密码）"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class UserBrief(BaseModel):
    """用户简要信息（用于嵌套场景）"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    full_name: Optional[str] = None


# ——— Auth Schemas ————————————————————————————————————————————————————

class Token(BaseModel):
    """JWT Token 响应（仅 access_token，兼容旧接口）"""
    access_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    """完整 Token 响应（包含 access_token + refresh_token）"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str


class TokenPayload(BaseModel):
    """JWT Token Payload"""
    sub: str  # user_id
    exp: Optional[int] = None
    type: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LogoutRequest(BaseModel):
    """登出请求"""
    token: str
