"""
API Key 模型
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class APIKey(Base):
    """
    API Key 表

    字段:
    - id: UUID 主键
    - user_id: 所属用户 ID
    - key_hash: SHA256 哈希后的 key（不存储明文）
    - key_prefix: key 前缀（sk-xxx，用于显示识别）
    - name: 密钥名称（可选）
    - is_active: 是否启用
    - created_at: 创建时间
    - last_used_at: 最后使用时间
    - expires_at: 过期时间（可选，None 表示永不过期）
    """

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 hex
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)  # 显示前缀 sk-xxx
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 密钥名称
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_api_keys_user_id", "user_id"),
        Index("ix_api_keys_key_hash", "key_hash"),
    )

    def __repr__(self) -> str:
        return f"<APIKey {self.key_prefix} ({self.name or 'unnamed'})>"
