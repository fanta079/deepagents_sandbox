"""
SQLite + SQLAlchemy 数据库配置

使用 async SQLAlchemy 以配合 FastAPI 异步路由
"""

from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# 数据库文件路径（项目根目录下）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'fastapi_project.db')}",
)

# ——— Async Engine & Session ———————————————————————————————————————————

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

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
