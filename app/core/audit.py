"""
操作审计日志

记录用户在 API 上的关键操作（登录、登出、创建/删除资源等），
用于安全审计和问题排查。
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """
    审计日志表

    记录：
    - user_id:操作用户（可为空，匿名操作）
    - action: 操作名称（如 "login", "create_task", "delete_user"）
    - resource: 资源类型（如 "user", "task"）
    - resource_id: 资源 ID（可选）
    - details: 额外详情（JSON）
    - ip_address: 请求来源 IP
    - user_agent: 浏览器客户端信息（可选）
    - created_at: 操作时间
    """

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(Text, nullable=True)  # JSON stored as text
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_audit_resource_action", "resource", "action"),
        Index("ix_audit_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.resource}/{self.resource_id} by {self.user_id}>"


def log_action(
    db,
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """
    创建并保存一条审计日志。

    Args:
        db: AsyncSession
        action: 操作名称
        resource: 资源类型
        resource_id: 资源 ID
        user_id: 操作用户 ID
        details: 额外信息 dict
        ip_address: 客户端 IP
        user_agent: 客户端 UA

    Returns:
        AuditLog 实例（需外部 commit）
    """
    import json

    audit = AuditLog(
        action=action,
        resource=resource,
        resource_id=resource_id,
        user_id=user_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit)
    return audit
