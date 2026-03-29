"""
OpenTelemetry 链路追踪配置

支持可选启用（OTEL_ENABLED=False 时完全不初始化）。
使用 BatchSpanProcessor + OTLP Exporter，支持连接失败时优雅降级。
"""

from __future__ import annotations

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_tracer: Optional[object] = None


def setup_tracing(service_name: Optional[str] = None) -> Optional[object]:
    """
    初始化 OpenTelemetry 追踪。

    仅在 settings.OTEL_ENABLED=True 时生效。
    OTLP Exporter 连接失败时记录警告但不抛出异常。

    Args:
        service_name: 服务名称（默认使用 settings.OTEL_SERVICE_NAME）

    Returns:
        Tracer 实例，追踪未启用时返回 None
    """
    global _tracer

    if not getattr(settings, "OTEL_ENABLED", False):
        logger.info("OpenTelemetry 追踪未启用（OTEL_ENABLED=False）")
        return None

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.semconv.resource import ResourceAttributes

        name = service_name or getattr(settings, "OTEL_SERVICE_NAME", "deepagents")
        version = getattr(settings, "APP_VERSION", "1.0.0")

        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: name,
            ResourceAttributes.SERVICE_VERSION: version,
        })

        provider = TracerProvider(resource=resource)

        # 尝试配置 OTLP Exporter
        endpoint = getattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
            logger.info(f"✅ OpenTelemetry 追踪已启用，导出至 {endpoint}")
        except Exception as otlp_err:
            logger.warning(f"⚠️ OTLP Exporter 初始化失败（{otlp_err}），追踪仅在内存中生效")

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(name)
        return _tracer

    except ImportError as e:
        logger.warning(f"⚠️ OpenTelemetry 依赖未安装（{e}），追踪功能不可用")
        return None
    except Exception as e:
        logger.warning(f"⚠️ OpenTelemetry 初始化失败（{e}），追踪功能不可用")
        return None


def get_tracer():
    """
    获取已初始化的 Tracer。

    如果追踪未初始化（或 setup_tracing 返回 None），返回 None。
    """
    global _tracer
    if _tracer is None:
        return setup_tracing()
    return _tracer
