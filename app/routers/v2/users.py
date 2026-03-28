"""
用户管理路由 v2 — 批量操作 + 增强功能

路径前缀: /api/v2/users
"""

from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import User
from app.schemas import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/api/v2/users", tags=["users"])


# ——— Schemas ————————————————————————————————————————————————————————————————

class UserBatchDelete(BaseModel):
    """批量删除用户请求"""
    user_ids: List[str]


class UserBatchUpdate(BaseModel):
    """批量更新用户请求"""
    user_ids: List[str]
    is_active: Optional[bool] = None


# ——— Create ————————————————————————————————————————————————————————————————

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_v2(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """创建新用户"""
    stmt = select(User).where(User.username == user_in.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    stmt = select(User).where(User.email == user_in.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ——— Read（分页 + 搜索）———————————————————————————————————————————

@router.get("/", response_model=list[UserResponse])
async def list_users_v2(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    search: Optional[str] = Query(None, description="按用户名搜索（模糊匹配）"),
    db: AsyncSession = Depends(get_db),
):
    """查询用户列表（分页 + 搜索）"""
    skip = (page - 1) * page_size

    stmt = select(User)

    if search:
        stmt = stmt.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )

    stmt = stmt.offset(skip).limit(page_size).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_v2(user_id: str, db: AsyncSession = Depends(get_db)):
    """根据 ID 获取单个用户"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


# ——— Update ————————————————————————————————————————————————————————————————

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_v2(
    user_id: str,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新用户信息（部分更新）"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


# ——— Delete ————————————————————————————————————————————————————————————————

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_v2(user_id: str, db: AsyncSession = Depends(get_db)):
    """删除用户"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.delete(user)
    await db.commit()


# ——— v2 批量操作 ————————————————————————————————————————————

@router.post("/batch/delete", status_code=status.HTTP_204_NO_CONTENT)
async def batch_delete_users(
    request: UserBatchDelete,
    db: AsyncSession = Depends(get_db),
):
    """批量删除用户"""
    stmt = select(User).where(User.id.in_(request.user_ids))
    result = await db.execute(stmt)
    users = result.scalars().all()

    for user in users:
        await db.delete(user)

    await db.commit()


@router.patch("/batch/update", response_model=list[UserResponse])
async def batch_update_users(
    request: UserBatchUpdate,
    db: AsyncSession = Depends(get_db),
):
    """批量更新用户状态"""
    stmt = select(User).where(User.id.in_(request.user_ids))
    result = await db.execute(stmt)
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="未找到指定用户")

    for user in users:
        if request.is_active is not None:
            user.is_active = request.is_active

    await db.commit()

    for user in users:
        await db.refresh(user)

    return users


@router.get("/batch/exists", response_model=dict)
async def check_users_exist(
    user_ids: str = Query(..., description="用户ID列表，逗号分隔"),
    db: AsyncSession = Depends(get_db),
):
    """批量检查用户是否存在"""
    ids = [uid.strip() for uid in user_ids.split(",") if uid.strip()]
    stmt = select(User.id).where(User.id.in_(ids))
    result = await db.execute(stmt)
    existing_ids = set(row[0] for row in result.fetchall())

    return {
        "exists": {uid: uid in existing_ids for uid in ids},
        "all_exist": len(existing_ids) == len(ids),
    }
