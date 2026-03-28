"""
Task Pydantic Schemas — 请求/响应模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from app.models.task import TaskStatus, TaskPriority


# ——— Base ————————————————————————————————————————————————————————————————

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务详细描述")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="优先级")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")


# ——— Create ————————————————————————————————————————————————————————————————

class TaskCreate(TaskBase):
    """创建任务时的请求体"""
    owner_id: str = Field(..., description="所属用户 ID")
    max_retries: int = Field(3, ge=0, le=10, description="最大重试次数")


# ——— Update / Status ————————————————————————————————————————————————

class TaskUpdate(BaseModel):
    """更新任务时的请求体"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    progress: Optional[int] = Field(None, ge=0, le=100)
    tags: Optional[List[str]] = Field(None, description="标签列表")


class TaskStatusUpdate(BaseModel):
    """只更新任务状态"""
    status: TaskStatus = Field(..., description="新状态")
    result: Optional[str] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息（失败时填）")
    progress: Optional[int] = Field(None, ge=0, le=100)


# ——— Response ————————————————————————————————————————————————————————————————

class TaskResponse(TaskBase):
    """任务响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: TaskStatus
    result: Optional[str] = None
    error: Optional[str] = None
    progress: int
    retry_count: int
    max_retries: int
    owner_id: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskBrief(BaseModel):
    """任务简要信息"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    status: TaskStatus
    priority: TaskPriority
    progress: int
