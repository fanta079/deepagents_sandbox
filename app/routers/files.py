"""
文件上传/下载路由
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(prefix="/api/v1/files", tags=["files"])


# 确保上传目录存在
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp",  # 图片
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",   # 文档
    ".txt", ".csv", ".json", ".xml",            # 文本
    ".zip", ".tar", ".gz", ".rar",              # 压缩包
    ".mp3", ".wav", ".mp4", ".avi",              # 音视频
}


def is_allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
):
    """
    上传单个文件

    POST /api/v1/files/upload
    """
    # 检查文件大小（默认 10MB）
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    file.file.seek(0, 2)  # 移动到文件末尾
    size = file.file.tell()
    file.file.seek(0)     # 恢复到开头

    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制（最大 {settings.MAX_FILE_SIZE_MB}MB）",
        )

    # 检查文件类型
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持的文件类型，仅支持: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # 生成唯一文件名
    ext = Path(file.filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_name

    # 写入文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "filename": unique_name,
        "original_filename": file.filename,
        "size": size,
        "url": f"/api/v1/files/{unique_name}",
    }


@router.get("/{filename}")
async def download_file(filename: str):
    """
    下载文件

    GET /api/v1/files/{filename}
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(filename: str):
    """
    删除上传的文件

    DELETE /api/v1/files/{filename}
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")

    file_path.unlink()
