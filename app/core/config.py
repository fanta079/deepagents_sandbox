import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Project"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ——— JWT 配置 ——————————————————————————————————————————
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ——— SMTP 邮件配置 ——————————————————————————————————————
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@example.com"

    # ——— Webhook 配置 ——————————————————————————————————————
    WEBHOOK_URL: str = ""

    # ——— OpenSandbox 沙箱配置 ——————————————————————————————
    OPENSANDBOX_API_KEY: str = ""
    OPENSANDBOX_DOMAIN: str = "api.opensandbox.io"
    OPENSANDBOX_IMAGE: str = "ubuntu"

    # ——— 沙箱资源限制配置 ——————————————————————————————
    SANDBOX_TIMEOUT: int = 30          # seconds
    SANDBOX_MEMORY_LIMIT: str = "256mb"
    SANDBOX_CPU_LIMIT: float = 1.0

    # ——— 文件上传配置 ——————————————————————————————————————
    UPLOAD_DIR: str = "app/uploads"
    MAX_FILE_SIZE_MB: int = 10

    # ——— Redis 配置 ——————————————————————————————————————————
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # ——— 日志配置 ——————————————————————————————————————————
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" | "text"
    LOG_JSON_FILE: Optional[str] = None  # JSON 日志文件路径，留空则仅输出到控制台

    # ——— 存储配置 ——————————————————————————————————————————
    STORAGE_TYPE: str = "local"  # "local" | "s3"
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT: Optional[str] = None
    S3_PUBLIC_URL_BASE: Optional[str] = None

    # ——— Agent 上下文配置 ——————————————————————————————————
    MAX_CONTEXT_MESSAGES: int = 50   # 最大上下文消息数
    MAX_CONTEXT_TOKENS: int = 4000   # 最大 token 数（估算）

    # ——— API Key 配置 ——————————————————————————————————————————
    API_KEY_ENABLED: bool = True  # 是否启用 API Key 认证（开发时可关闭）

    # ——— OpenTelemetry 配置 ——————————————————————————————————
    OTEL_SERVICE_NAME: str = "deepagents"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_ENABLED: bool = False  # 是否启用链路追踪

    # ——— LangSmith 配置（可选）———————————————————————————————————
    LANGCHAIN_TRACING: bool = False  # 是否启用 LangSmith LLM 追踪
    LANGCHAIN_PROJECT: str = "deepagents"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""

    # ——— PostgreSQL 生产配置（SQLite 适合开发，生产推荐 PostgreSQL）——
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "deepagents"

    # ——— 数据库配置 ——————————————————————————————————————————————
    DATABASE_URL: Optional[str] = None  # 优先使用 DATABASE_URL 环境变量

    class Config:
        env_file = ".env"


settings = Settings()


def get_database_url() -> str:
    """
    获取数据库连接 URL。

    优先使用 DATABASE_URL 环境变量（支持 SQLite 和 PostgreSQL）。
    未设置时根据 POSTGRES_* 配置拼接 PostgreSQL URL。
    """
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    if settings.POSTGRES_PASSWORD:
        return (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
    # 默认使用 SQLite（开发模式）
    return f"sqlite+aiosqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fastapi_project.db')}"
