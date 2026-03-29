"""
统一异常类定义

提供业务异常基类及常用异常类型
"""

from __future__ import annotations
from typing import Any, Optional


class AppException(Exception):
    """应用异常基类

    Args:
        code: 错误码，用于前端识别错误类型
        message: 人类可读的错误信息
        status_code: HTTP 状态码，默认 400
        details: 附加细节（如字段校验错误列表）
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(AppException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(code="NOT_FOUND", message=message, status_code=404)


class UnauthorizedException(AppException):
    """未授权（未登录或 Token 无效）"""

    def __init__(self, message: str = "未授权，请先登录") -> None:
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401)


class ForbiddenException(AppException):
    """禁止访问（无权限）"""

    def __init__(self, message: str = "无权访问该资源") -> None:
        super().__init__(code="FORBIDDEN", message=message, status_code=403)


class ValidationException(AppException):
    """数据校验失败"""

    def __init__(self, message: str = "数据校验失败", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=422, details=details)
