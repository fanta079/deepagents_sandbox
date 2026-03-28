"""
全局异常处理器

将 AppException 映射为统一格式的 JSON 响应
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """捕获 AppException，返回统一格式的 JSON 响应

    Args:
        request: FastAPI 请求对象
        exc: 业务异常实例

    Returns:
        JSONResponse，包含 code 和 message 字段
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
        },
    )
