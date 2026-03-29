"""
Prometheus metrics 端点
"""
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(prefix="/metrics", tags=["monitoring"])

# 定义 metrics
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)
active_sessions = Gauge(
    "active_sessions",
    "Number of active sessions"
)
agent_invocations = Counter(
    "agent_invocations_total",
    "Total agent invocations",
    ["backend"]
)
task_count = Gauge(
    "tasks_total",
    "Total number of tasks",
    ["status"]
)


@router.get("/", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics 采集端点
    GET /metrics
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
