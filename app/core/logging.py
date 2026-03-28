"""
结构化日志配置

提供 JSONFormatter，支持将日志输出为 JSON 格式，
方便日志收集系统（如 ELK、Loki）解析。
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional


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

    # Console handler
    if text_stream:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
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
