"""
超时中间件
"""
import asyncio
import uuid
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class TimeoutMiddleware(BaseHTTPMiddleware):
    """请求超时中间件 — 超过指定时间返回 504"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await asyncio.wait_for(
                call_next(request),
                timeout=30.0
            )
            return response
        except asyncio.TimeoutError:
            return JSONResponse(
                {"detail": "Request timeout"},
                status_code=504
            )


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    请求 ID 追踪中间件

    - 优先使用请求头 X-Request-ID
    - 若无则自动生成 UUID
    - 将请求 ID 注入 request.state.request_id
    - 在响应头中返回 X-Request-ID
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
