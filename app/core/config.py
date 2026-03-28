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

    # ——— 文件上传配置 ——————————————————————————————————————
    UPLOAD_DIR: str = "app/uploads"
    MAX_FILE_SIZE_MB: int = 10

    # ——— Redis 配置 ——————————————————————————————————————————
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
