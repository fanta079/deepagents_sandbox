"""
GraphQL Types — Strawberry type definitions
"""

import strawberry
from typing import Optional, List
from datetime import datetime


@strawberry.type
class UserType:
    id: str
    username: str
    email: str
    created_at: datetime


@strawberry.type
class TaskType:
    id: str
    title: str
    status: str
    priority: str
    created_at: datetime
    updated_at: Optional[datetime]


@strawberry.type
class AgentResponse:
    message: str
    success: bool


@strawberry.type
class TaskStatusType:
    """任务状态统计"""
    pending: int
    running: int
    success: int
    failed: int
    cancelled: int


@strawberry.type
class HealthType:
    status: str
    version: str
