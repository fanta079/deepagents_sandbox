"""
结构化日志配置

提供 JSONFormatter，支持将日志输出为 JSON 格式，
方便日志收集系统（如 ELK、Loki）解析。
"""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Optional

# ——— 日志脱敏 —————————————————————————————————————————————

SENSITIVE_KEYS = ["password", "token", "secret", "api_key", "Authorization", "access_token", "refresh_token"]


def mask_sensitive(data: str) -> str:
    """
    替换日志中的敏感字段值为 ***MASKED***。

    支持格式:
    - "password": "secret123"
    - 'password': 'secret123'
    - password="secret123"
    - Authorization: Bearer xxx
    """
    for key in SENSITIVE_KEYS:
        # JSON / dict-style: key": "value" 或 key': 'value'
        pattern = rf'({key}["\']?\s*[:=]\s*["\']?)([^"\'&\s]+)'
        data = re.sub(pattern, r'\1***MASKED***', data, flags=re.IGNORECASE)
    return data


class SensitiveFormatter(logging.Formatter):
    """格式化器：对每条日志消息执行敏感字段脱敏"""

    def format(self, record: logging.LogRecord) -> str:
        record.msg = mask_sensitive(str(record.msg))
        if record.args:
            record.args = tuple(mask_sensitive(str(a)) for a in record.args)
        return super().format(record)


# ——— JSON Formatter —————————————————————————————————————————————

class JSONFormatter(logging.Formatter):
    """
    将日志格式化为 JSON 字符串。
    
    输出字段：
    - time: ISO 格式时间戳（UTC）
    - level: 日志级别（INFO、ERROR 等）
    - message: 日志消息
    - module: 日志模块名
    - funcName: 函数名（如果可用）
    - lineno: 行号（如果可用）
    - exception: 异常信息（如果有 exc_info）
    - extra: 额外字段（如果通过 extra 传入）
    """

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }

        if record.funcName and record.funcName != "<module>":
            log_data["funcName"] = record.funcName
        if record.lineno:
            log_data["lineno"] = record.lineno

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if self.include_extra:
            # 支持通过 extra={} 传入额外字段
            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in (
                    "name", "msg", "args", "created", "filename", "funcName",
                    "levelname", "levelno", "lineno", "module", "msecs",
                    "pathname", "process", "processName", "relativeCreated",
                    "stack_info", "exc_info", "exc_text", "thread", "threadName",
                    "message", "taskName",
                )
            }
            if extra_fields:
                log_data["extra"] = extra_fields

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    json_file: Optional[str] = None,
    text_stream: Optional[bool] = True,
) -> None:
    """
    配置全局日志输出。
    
    Args:
        level: 日志级别（DEBUG、INFO、WARNING、ERROR）
        log_format: 格式类型，"json" 或 "text"
        json_file: JSON 日志文件路径（可选，写入文件时使用 JSON 格式）
        text_stream: 是否输出到 stdout/stderr（文本格式）
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 避免重复添加 handler
    if root_logger.handlers:
        root_logger.handlers.clear()

    if log_format == "json":
        formatter = JSONFormatter(include_extra=True)
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler (always use SensitiveFormatter for privacy)
    if text_stream:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(SensitiveFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        root_logger.addHandler(console_handler)

    # JSON file handler（可选）
    if json_file:
        file_handler = logging.FileHandler(json_file, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter(include_extra=True))
        root_logger.addHandler(file_handler)

    # 抑制第三方库噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("slowapi").setLevel(logging.WARNING)


# ——— API 请求日志中间件 —————————————————————————————————————————————

import time
import logging as stdlib_logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger_api = stdlib_logging.getLogger("api.request")


class APIRequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Starlette 中间件，记录每个 API 请求的：
    - 请求方法 + 路径
    - User-Agent
    - 请求体大小
    - 响应状态码
    - 响应体大小
    - 请求耗时
    """

    # 排除的路径（避免记录 WebSocket、SSE 等）
    EXCLUDE_PATHS = {"/ws", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in self.EXCLUDE_PATHS:
            return await call_next(request)

        method = request.method
        user_agent = request.headers.get("user-agent", "unknown")
        content_length = request.headers.get("content-length", "0")

        # 读取请求体（如果需要）
        request_body: Optional[bytes] = None
        if content_length and int(content_length) > 0 and int(content_length) < 1024 * 1024:
            # 仅记录 < 1MB 的请求体
            try:
                request_body = await request.body()
            except Exception:
                request_body = None

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        response_body_size = response.headers.get("content-length", "0")
        status_code = response.status_code

        log_data = {
            "method": method,
            "path": path,
            "status": status_code,
            "user_agent": user_agent,
            "request_size": len(request_body) if request_body else int(content_length),
            "response_size": int(response_body_size) if response_body_size.isdigit() else 0,
            "duration_ms": round(duration_ms, 2),
        }

        if request_body:
            log_data["request_body"] = mask_sensitive(request_body.decode("utf-8", errors="replace"))

        logger_api.info(
            "API Request: %s %s | status=%d | ua=%s | "
            "req_size=%d bytes | resp_size=%d bytes | duration=%.2fms",
            method, path, status_code, user_agent,
            log_data["request_size"], log_data["response_size"], log_data["duration_ms"],
        )

        return response

