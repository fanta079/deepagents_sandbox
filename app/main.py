"""
FastAPI 主入口

启动命令:
    uvicorn app.main:app --reload --port 8000
"""

import asyncio
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi.errors import RateLimitExceeded
from strawberry.fastapi import GraphQLRouter

from app.core.config import settings
from app.core.database import init_db
from app.core.errors import app_exception_handler
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.core.middleware import TimeoutMiddleware
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.graphql.schema import schema as graphql_schema
from app.i18n.middleware import I18nMiddleware
from app.routers import agent, example, sse, users, tasks, files, websocket, auth, apikeys
from app.routers.v2 import users as v2_users, tasks as v2_tasks, agent as v2_agent
from app.routers.metrics import router as metrics_router
from app.routers.rag import router as rag_router
from app.routers.admin import router as admin_router


# ——— 优雅关闭 ———————————————————————————————————————————————————

shutdown_event: asyncio.Event | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化 + 关闭时清理"""
    global shutdown_event

    setup_logging(
        level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        json_file=settings.LOG_JSON_FILE,
        text_stream=True,
    )

    # OpenTelemetry 追踪初始化
    from app.core.tracing import setup_tracing
    setup_tracing()

    # LangSmith LLM 追踪初始化（可选）
    from app.core.langsmith import setup_langsmith
    setup_langsmith()

    # FastAPI 自动注入请求追踪
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        pass  # opentelemetry-instrumentation-fastapi 未安装

    # SQLAlchemy 自动注入数据库查询追踪
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from app.core.database import engine
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    except ImportError:
        pass  # opentelemetry-instrumentation-sqlalchemy 未安装
    except Exception:
        pass

    # Redis 自动注入缓存追踪
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor().instrument()
    except ImportError:
        pass  # opentelemetry-instrumentation-redis 未安装
    except Exception:
        pass

    await init_db()

    # 注册信号处理器
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def _shutdown_signal_handler():
        asyncio.create_task(_graceful_shutdown())

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _shutdown_signal_handler)
        except NotImplementedError:
            # Windows 不支持 add_signal_handler
            pass

    yield

    # 关闭时清理
    await _graceful_shutdown()


async def _graceful_shutdown():
    """执行优雅关闭"""
    if shutdown_event and shutdown_event.is_set():
        return
    shutdown_event = shutdown_event or asyncio.Event()
    shutdown_event.set()

    # 关闭 Agent 沙箱
    try:
        from app.sandbox.agent_runner import shutdown_agent
        await shutdown_agent()
    except Exception:
        pass

    # 关闭 OpenTelemetry 追踪
    try:
        from opentelemetry import trace
        provider = trace.get_tracer_provider()
        if hasattr(provider, "shutdown"):
            provider.shutdown()
    except Exception:
        pass

    # 关闭数据库连接
    try:
        from app.core.database import engine
        await engine.dispose()
    except Exception:
        pass

    # 关闭 Redis 连接
    try:
        from app.core.cache import _redis_client, _use_redis
        if _use_redis and _redis_client:
            _redis_client.close()
    except Exception:
        pass


app = FastAPI(
    title="DeepAgents API",
    version="1.2.0",
    description="""
    ## DeepAgents - Multi-Sandbox Agent Service

    ### Features
    - 🤖 Agent Chat with SSE streaming
    - 🔐 JWT Authentication with Refresh Token
    - 📋 Task Queue with Celery
    - 💾 Redis Caching with Token Blacklist
    - 📁 File Upload with Cloud Storage
    - 🐳 Docker & Kubernetes Ready
    - 🌍 Internationalization (i18n) Support
    - 📊 GraphQL API
    - ✅ Health Check with DB/Redis status

    ### Authentication
    - Register: `POST /api/v1/users/` → `{"username":"test","email":"test@example.com","password":"secret123"}`
    - Login: `POST /api/v1/auth/login` → `{"username":"test","password":"secret123"}` → `{"access_token":"...","refresh_token":"..."}`
    - Refresh: `POST /api/v1/auth/refresh` → `{"refresh_token":"..."}`

    ### Task Lifecycle
    ```
    pending → running → success / failed / cancelled
    ```
    Only `failed` tasks can be retried (up to `max_retries` times).

    ### Rate Limits
    - Default: 100 req/min per IP
    - Agent endpoints: 10 req/min per IP
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ——— Rate Limiting ——————————————————————————————————————————————————————

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ——— Unified Exception Handler —————————————————————————————————————————

app.add_exception_handler(AppException, app_exception_handler)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """捕获所有未处理异常，返回统一错误格式"""
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": {},
                }
            },
        )
    # 记录未知异常但不暴露给客户端
    import logging
    logging.getLogger("app").exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "details": {},
            }
        },
    )


app.add_exception_handler(Exception, generic_exception_handler)

# ——— Middleware ————————————————————————————————————————————————————————————

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(I18nMiddleware)
app.add_middleware(TimeoutMiddleware)  # 请求超时中间件

# ——— API Versioned Routers ————————————————————————————————————————————

# v1 路由
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(users.router, tags=["Users"])
v1_router.include_router(tasks.router, tags=["Tasks"])
v1_router.include_router(agent.router, tags=["Agent"])
app.include_router(v1_router)

# v2 路由
v2_router = APIRouter(prefix="/api/v2")
v2_router.include_router(v2_users.router, tags=["Users"])
v2_router.include_router(v2_tasks.router, tags=["Tasks"])
v2_router.include_router(v2_agent.router, tags=["Agent"])
app.include_router(v2_router)

# ——— Other Routers ————————————————————————————————————————————————————

app.include_router(example.router)
app.include_router(sse.router)
app.include_router(files.router)
app.include_router(websocket.router)
app.include_router(auth.router)
app.include_router(apikeys.router)

# ——— Metrics Router ————————————————————————————————————————————————————

app.include_router(metrics_router)

# ——— Admin Router

app.include_router(admin_router)

# ——— RAG Router —————————————————————————————————————————————————————————

app.include_router(rag_router)


# ——— GraphQL Router ————————————————————————————————————————————————————————

graphql_app = GraphQLRouter(graphql_schema)
app.include_router(graphql_app, prefix="/graphql")


# ——— 根路径 ————————————————————————————————————————————————————————————————

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health():
    """
    健康检查接口

    返回应用状态及数据库、Redis 连通性。
    任何一项检查失败返回 503。
    """
    checks = {
        "status": "ok",
        "database": await _check_database(),
        "redis": await _check_redis(),
    }
    if not all(c == "ok" for c in checks.values()):
        from fastapi import HTTPException
        raise HTTPException(503, checks)
    return checks


async def _check_database() -> str:
    """检查数据库连接"""
    try:
        from sqlalchemy import text
        from app.core.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


async def _check_redis() -> str:
    """检查 Redis 连接"""
    try:
        from app.core.cache import _redis_client, _use_redis
        if _use_redis and _redis_client:
            _redis_client.ping()
        return "ok"
    except Exception:
        return "error"


# ——— 详细健康检查端点 ——————————————————————————————————————————————————————

from datetime import datetime


async def _check_sandbox() -> str:
    """检查沙箱连接"""
    try:
        from app.sandbox.agent_runner import get_agent
        await get_agent(backend_type="opensandbox")
        return "ok"
    except Exception:
        return "error"


async def _check_celery() -> str:
    """检查 Celery 连接"""
    try:
        from app.tasks.celery_app import is_celery_available
        return "ok" if is_celery_available else "unavailable"
    except Exception:
        return "error"


@app.get("/health/detailed")
async def health_check_detailed():
    """
    详细健康检查

    返回所有依赖服务的状态：API、数据库、Redis、沙箱、Celery。
    """
    checks = {
        "api": "ok",
        "database": await _check_database(),
        "redis": await _check_redis(),
        "sandbox": await _check_sandbox(),
        "celery": await _check_celery(),
    }
    overall = "healthy" if all(v in ("ok", "unavailable") for v in checks.values()) else "degraded"
    return {
        "status": overall,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }
