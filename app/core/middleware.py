"""
超时中间件
"""
import asyncio
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
