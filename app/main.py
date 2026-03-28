"""
FastAPI 主入口

启动命令:
    uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from strawberry.fastapi import GraphQLRouter

from app.core.config import settings
from app.core.database import init_db
from app.core.errors import app_exception_handler
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.graphql.schema import schema as graphql_schema
from app.i18n.middleware import I18nMiddleware
from app.routers import agent, example, sse, users, tasks, files, websocket, auth
from app.routers.v2 import users as v2_users, tasks as v2_tasks, agent as v2_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库 + 配置日志"""
    setup_logging(
        level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        json_file=settings.LOG_JSON_FILE,
        text_stream=True,
    )
    await init_db()
    yield


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

# ——— Middleware ————————————————————————————————————————————————————————————

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(I18nMiddleware)

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
    return {"status": "ok"}
