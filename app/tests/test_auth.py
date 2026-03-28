"""
认证 API 测试 — 登录/注册/Refresh Token/登出
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """测试用户注册成功"""
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """测试用户名重复注册失败"""
    payload = {
        "username": "dupuser",
        "email": "dup1@example.com",
        "password": "password123",
    }
    await client.post("/api/v1/users/", json=payload)

    response = await client.post(
        "/api/v1/users/",
        json={**payload, "email": "dup2@example.com"},
    )
    assert response.status_code == 400
    assert "用户名已存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """测试邮箱重复注册失败"""
    payload = {
        "username": "user1",
        "email": "sameemail@example.com",
        "password": "password123",
    }
    await client.post("/api/v1/users/", json=payload)

    response = await client.post(
        "/api/v1/users/",
        json={**payload, "username": "user2"},
    )
    assert response.status_code == 400
    assert "邮箱已存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """测试无效邮箱格式"""
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "badmail",
            "email": "not-an-email",
            "password": "password123",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """测试密码过短"""
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "shortpw",
            "email": "short@example.com",
            "password": "12345",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success_returns_tokens(client: AsyncClient):
    """测试登录成功返回 access_token 和 refresh_token"""
    await client.post(
        "/api/v1/users/",
        json={
            "username": "logintest",
            "email": "logintest@example.com",
            "password": "secret123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "logintest", "password": "secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    # JWT 格式校验（3段）
    assert len(data["access_token"].split(".")) == 3
    assert len(data["refresh_token"].split(".")) == 3


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """测试密码错误返回 401"""
    await client.post(
        "/api/v1/users/",
        json={
            "username": "wrongpwuser",
            "email": "wrongpw@example.com",
            "password": "correct",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "wrongpwuser", "password": "wrong"},
    )
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """测试用户不存在返回 401"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "notexist", "password": "anypassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient):
    """测试登录已禁用用户返回 403"""
    # 创建用户
    create_resp = await client.post(
        "/api/v1/users/",
        json={
            "username": "inactiveuser",
            "email": "inactive@example.com",
            "password": "password123",
        },
    )
    user_id = create_resp.json()["id"]

    # 禁用用户
    await client.patch(
        f"/api/v1/users/{user_id}",
        json={"is_active": False},
    )

    # 尝试登录
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "inactiveuser", "password": "password123"},
    )
    assert response.status_code == 403
    assert "已被禁用" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient):
    """测试 Refresh Token 换取新的 Access Token"""
    await client.post(
        "/api/v1/users/",
        json={
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "password123",
        },
    )

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "refreshuser", "password": "password123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # 新旧 refresh_token 不同（每次 refresh 都轮转）
    assert data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """测试无效 Refresh Token 返回 401"""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.jwt.token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_wrong_type(client: AsyncClient):
    """测试用 Access Token 当 Refresh Token 返回 401"""
    await client.post(
        "/api/v1/users/",
        json={
            "username": "tokentypeuser",
            "email": "tokentype@example.com",
            "password": "password123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "tokentypeuser", "password": "password123"},
    )
    access_token = login_resp.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_blacklists_token(client: AsyncClient):
    """测试登出后 Token 被加入黑名单"""
    await client.post(
        "/api/v1/users/",
        json={
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "password123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "logoutuser", "password": "password123"},
    )
    access_token = login_resp.json()["access_token"]

    # 登出
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"token": access_token},
    )
    assert logout_resp.status_code == 200

    # 再次使用同一 token 登出（幂等，仍返回 200）
    logout_resp2 = await client.post(
        "/api/v1/auth/logout",
        json={"token": access_token},
    )
    assert logout_resp2.status_code == 200


@pytest.mark.asyncio
async def test_logout_invalid_token(client: AsyncClient):
    """测试登出无效 Token 返回 401"""
    response = await client.post(
        "/api/v1/auth/logout",
        json={"token": "not.a.valid.jwt"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_token_contains_jti(client: AsyncClient):
    """测试 Access Token Payload 包含 jti（用于黑名单）"""
    await client.post(
        "/api/v1/users/",
        json={
            "username": "tknpayload",
            "email": "tknpayload@example.com",
            "password": "password123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "tknpayload", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # 解码 JWT payload（不使用验证）
    import base64
    import json as _json

    payload_b64 = token.split(".")[1]
    # 补齐 padding
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    payload = _json.loads(base64.urlsafe_b64decode(payload_b64))

    assert "jti" in payload
    assert "sub" in payload
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_refresh_token_contains_jti(client: AsyncClient):
    """测试 Refresh Token Payload 包含 jti"""
    await client.post(
        "/api/v1/users/",
        json={
            "username": "rftkn",
            "email": "rftkn@example.com",
            "password": "password123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "rftkn", "password": "password123"},
    )
    token = login_resp.json()["refresh_token"]

    import base64
    import json as _json

    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    payload = _json.loads(base64.urlsafe_b64decode(payload_b64))

    assert "jti" in payload
    assert payload["type"] == "refresh"
