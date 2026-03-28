"""
API 限流 — 使用 slowapi
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# 全局限流器（按 IP）
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """限流异常处理器"""
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"请求过于频繁，请稍后再试。限制: {exc.detail}",
        },
    )


def get_user_id(request: Request) -> str:
    """
    获取用户标识：登录用户用 user_id，未登录用 IP。
    用于 per-user 限流。
    """
    return request.state.user_id if hasattr(request.state, "user_id") else get_remote_address(request)


# per-user 限流器（登录后更严格）
user_limiter = Limiter(key_func=get_user_id)


def agent_rate_limit():
    """Agent 接口专用限流装饰器（10次/分钟）"""
    return limiter.limit("10/minute")
