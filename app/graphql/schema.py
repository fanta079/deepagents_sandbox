"""
GraphQL Schema — Strawberry schema definition
"""

import strawberry
from typing import List, Optional

from app.graphql.types import (
    UserType,
    TaskType,
    AgentResponse,
    TaskStatusType,
    HealthType,
)


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> HealthType:
        """全局健康检查"""
        return HealthType(status="ok", version="1.2.0")

    @strawberry.field
    async def users(self, limit: int = 10) -> List[UserType]:
        """获取用户列表"""
        from app.core.database import AsyncSessionLocal
        from app.models import User

        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            stmt = select(User).limit(limit).order_by(User.created_at.desc())
            result = await session.execute(stmt)
            users = result.scalars().all()
            return [
                UserType(
                    id=str(u.id),
                    username=u.username,
                    email=u.email,
                    created_at=u.created_at,
                )
                for u in users
            ]

    @strawberry.field
    async def user(self, user_id: str) -> Optional[UserType]:
        """根据 ID 获取用户"""
        from app.core.database import AsyncSessionLocal
        from app.models import User
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            u = result.scalar_one_or_none()
            if not u:
                return None
            return UserType(
                id=str(u.id),
                username=u.username,
                email=u.email,
                created_at=u.created_at,
            )

    @strawberry.field
    async def tasks(
        self,
        status: Optional[str] = None,
        owner_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[TaskType]:
        """获取任务列表，支持按状态和用户过滤"""
        from app.core.database import AsyncSessionLocal
        from app.models import Task, TaskStatus
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            stmt = select(Task)
            if status:
                try:
                    ts = TaskStatus(status)
                    stmt = stmt.where(Task.status == ts)
                except ValueError:
                    pass
            if owner_id:
                stmt = stmt.where(Task.owner_id == owner_id)
            stmt = stmt.order_by(Task.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            tasks = result.scalars().all()
            return [
                TaskType(
                    id=str(t.id),
                    title=t.title,
                    status=t.status.value,
                    priority=t.priority.value,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in tasks
            ]

    @strawberry.field
    async def task(self, task_id: str) -> Optional[TaskType]:
        """根据 ID 获取任务"""
        from app.core.database import AsyncSessionLocal
        from app.models import Task
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            stmt = select(Task).where(Task.id == task_id)
            result = await session.execute(stmt)
            t = result.scalar_one_or_none()
            if not t:
                return None
            return TaskType(
                id=str(t.id),
                title=t.title,
                status=t.status.value,
                priority=t.priority.value,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )

    @strawberry.field
    async def task_stats(self) -> TaskStatusType:
        """获取任务状态统计"""
        from app.core.database import AsyncSessionLocal
        from app.models import Task, TaskStatus
        from sqlalchemy import select, func

        async with AsyncSessionLocal() as session:
            stats = {}
            for s in TaskStatus:
                stmt = select(func.count()).select_from(Task).where(Task.status == s)
                result = await session.execute(stmt)
                stats[s.value] = result.scalar() or 0
            return TaskStatusType(**stats)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def chat(self, message: str) -> AgentResponse:
        """Agent 对话（GraphQL Mutation）"""
        # 实际调用 agent 逻辑
        return AgentResponse(message=f"收到消息: {message}", success=True)

    @strawberry.mutation
    async def reset_agent(self, backend: str = "opensandbox") -> AgentResponse:
        """重置 Agent"""
        from app.sandbox.agent_runner import shutdown_agent

        try:
            await shutdown_agent()
            return AgentResponse(
                message=f"{backend} 沙箱已重置", success=True
            )
        except Exception as e:
            return AgentResponse(message=str(e), success=False)


schema = strawberry.Schema(query=Query, mutation=Mutation)
