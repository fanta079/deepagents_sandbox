"""
JWT 安全工具函数
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """对密码进行 bcrypt 哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Access Token

    Args:
        data: 要编码进 token 的数据（通常包含 sub: user_id）
        expires_delta: 过期时间增量，默认 30 分钟

    Returns:
        JWT 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码并验证 JWT Token

    Args:
        token: JWT 字符串

    Returns:
        解码后的 payload，失败返回 None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Refresh Token

    Args:
        data: 要编码进 token 的数据（通常包含 sub: user_id）
        expires_delta: 过期时间增量，默认 7 天

    Returns:
        JWT 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> Optional[dict]:
    """验证并解码 JWT Refresh Token

    Args:
        token: JWT 字符串

    Returns:
        解码后的 payload，失败返回 None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


# ——— API Key 哈希 ————————————————————————————————————————————————

import hashlib


def hash_api_key(api_key: str) -> str:
    """
    对 API Key 进行 SHA256 哈希（不存储明文）

    Args:
        api_key: 原始 API Key

    Returns:
        SHA256 十六进制字符串
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    验证 API Key 是否匹配哈希值

    Args:
        plain_key: 原始 API Key
        hashed_key: 存储的 SHA256 哈希

    Returns:
        True = 匹配，False = 不匹配
    """
    return hash_api_key(plain_key) == hashed_key
