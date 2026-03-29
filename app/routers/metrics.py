"""
Prometheus metrics 端点
"""
from fastapi import APIRouter
from starlette.responses import Response

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

router = APIRouter(prefix="/metrics", tags=["monitoring"])

if PROMETHEUS_AVAILABLE:
    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"]
    )
    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration"
    )
    active_sessions = Gauge("active_sessions", "Number of active sessions")
    agent_invocations_total = Counter(
        "agent_invocations_total",
        "Total agent invocations",
        ["backend"]
    )
    tasks_total = Gauge("tasks_total", "Total number of tasks", ["status"])


@router.get("/")
async def metrics():
    """Prometheus metrics 抓取端点"""
    if not PROMETHEUS_AVAILABLE:
        return Response(content="# prometheus_client not installed", media_type="text/plain")
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
