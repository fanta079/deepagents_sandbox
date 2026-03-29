"""
API 版本信息端点
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["version"])


class VersionInfo(BaseModel):
    app_name: str
    version: str
    api_version: str


@router.get("/version", response_model=VersionInfo)
async def get_version():
    """获取 API 版本信息"""
    return VersionInfo(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        api_version="v1"
    )
