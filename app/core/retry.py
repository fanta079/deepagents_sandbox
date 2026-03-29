"""
重试装饰器
"""
import asyncio
from functools import wraps
from typing import Callable, TypeVar, ParamSpec
import logging

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    异步函数重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 初始重试延迟（秒）
        backoff: 退避倍数（delay * backoff^attempt）
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(
                            "async_retry: all %d attempts failed for %s: %s",
                            max_attempts, func.__name__, e
                        )
                        raise
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(
                        "async_retry: attempt %d/%d failed for %s: %s. "
                        "Retrying in %.1fs...",
                        attempt + 1, max_attempts, func.__name__, e, wait_time
                    )
                    await asyncio.sleep(wait_time)
            # 未发生时返回 None（理论上不会到达这里）
            return None  # type: ignore[return-value]
        return wrapper  # type: ignore[return-value]
    return decorator
