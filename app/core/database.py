"""
SQLite + SQLAlchemy 数据库配置

使用 async SQLAlchemy 以配合 FastAPI 异步路由。
支持 SQLite（开发）和 PostgreSQL（生产），通过 DATABASE_URL 或 POSTGRES_* 环境变量配置。
"""

from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_database_url

# ——— 数据库 URL ————————————————————————————————————————————————————

DATABASE_URL = get_database_url()

# ——— Async Engine & Session ———————————————————————————————————————————

_is_sqlite = "sqlite" in DATABASE_URL
_engine_kwargs = {
    "echo": False,
    "connect_args": {"check_same_thread": False} if _is_sqlite else {},
}
if not _is_sqlite:
    _engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600,
        # PostgreSQL 连接池额外配置
        "pool_pre_ping": True,
    })
engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ——— Base ————————————————————————————————————————————————————————————————

class Base(DeclarativeBase):
    pass


# ——— 依赖注入（FastAPI Depends） ————————————————————————————————————————

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：每个请求一个 session，请求结束后自动关闭"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ——— 初始化/删除表（开发阶段用） ————————————————————————————————————————

async def init_db():
    """创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """删除所有表（危险，仅开发用）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
