"""
FastAPI 主入口

启动命令:
    uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import init_db
from app.core.errors import app_exception_handler
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.routers import agent, example, sse, users, tasks, files, websocket, auth


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
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="DeepAgents FastAPI — 支持多沙箱后端的 AI Agent 服务",
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

# ——— Routers ————————————————————————————————————————————————————————————————

app.include_router(agent.router)
app.include_router(example.router)
app.include_router(sse.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(files.router)
app.include_router(websocket.router)
app.include_router(auth.router)


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
