"""
云存储抽象层

支持多种存储后端：
- LocalStorage: 本地文件系统
- S3Storage: AWS S3 / S3 兼容对象存储（MinIO、Cloudflare R2 等）
"""

import logging
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        """
        上传文件。

        Args:
            key: 对象键（如 "uploads/abc123.png"）
            data: 文件内容字节
            content_type: MIME 类型（可选）

        Returns:
            访问 URL 或路径
        """
        pass

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """下载文件内容"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除文件"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    def get_url(self, key: str) -> str:
        """获取文件的访问 URL"""
        pass


class LocalStorage(StorageBackend):
    """本地文件系统存储"""

    def __init__(self, base_path: str = "app/uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        return self.base_path / key.lstrip("/")

    async def upload(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        await self._write(path, data)
        logger.info("File uploaded (local): %s", key)
        return self.get_url(key)

    async def _write(self, path: Path, data: bytes) -> None:
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, path.write_bytes, data)

    async def download(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, path.read_bytes)

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, path.unlink)
            logger.info("File deleted (local): %s", key)

    async def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def get_url(self, key: str) -> str:
        return f"/files/{key.lstrip('/')}"


class S3Storage(StorageBackend):
    """AWS S3 / S3 兼容对象存储"""

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        public_url_base: Optional[str] = None,
    ):
        self.bucket = bucket
        self.region = region
        self.endpoint = endpoint
        self.access_key = access_key or os.getenv("AWS_ACCESS_KEY_ID", "")
        self.secret_key = secret_key or os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.public_url_base = public_url_base or f"https://{bucket}.s3.{region}.amazonaws.com"
        self._client = None

    @property
    def client(self):
        """懒加载 S3 客户端"""
        if self._client is None:
            import boto3
            kwargs = {
                "region_name": self.region,
                "aws_access_key_id": self.access_key,
                "aws_secret_access_key": self.secret_key,
            }
            if self.endpoint:
                kwargs["endpoint_url"] = self.endpoint
            self._client = boto3.client("s3", **kwargs)
        return self._client

    async def upload(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        import asyncio
        extra = {"ContentType": content_type} if content_type else {}
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra),
        )
        logger.info("File uploaded (S3): %s", key)
        return self.get_url(key)

    async def download(self, key: str) -> bytes:
        import asyncio

        def _download():
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()

        return await asyncio.get_event_loop().run_in_executor(None, _download)

    async def delete(self, key: str) -> None:
        import asyncio
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.client.delete_object(Bucket=self.bucket, Key=key),
        )
        logger.info("File deleted (S3): %s", key)

    async def exists(self, key: str) -> bool:
        import asyncio

        def _check():
            try:
                self.client.head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False

        return await asyncio.get_event_loop().run_in_executor(None, _check)

    def get_url(self, key: str) -> str:
        if self.public_url_base:
            return f"{self.public_url_base.rstrip('/')}/{key.lstrip('/')}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key.lstrip('/')}"


def get_storage() -> StorageBackend:
    """
    工厂函数：根据配置返回对应存储后端实例。
    
    目前支持：
    - "local": LocalStorage
    - "s3": S3Storage（需配置 AWS 相关环境变量）
    """
    from app.core.config import settings
    storage_type = getattr(settings, "STORAGE_TYPE", "local")

    if storage_type == "s3":
        return S3Storage(
            bucket=getattr(settings, "S3_BUCKET", ""),
            region=getattr(settings, "S3_REGION", "us-east-1"),
            endpoint=getattr(settings, "S3_ENDPOINT", None),
            access_key=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            secret_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            public_url_base=getattr(settings, "S3_PUBLIC_URL_BASE", None),
        )

    return LocalStorage(base_path=getattr(settings, "UPLOAD_DIR", "app/uploads"))
