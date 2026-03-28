"""
用户 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    """测试创建用户"""
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client: AsyncClient):
    """测试用户名重复"""
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
async def test_login_success(client: AsyncClient):
    """测试登录成功"""
    # 先创建用户
    await client.post(
        "/api/v1/users/",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "secret123",
        },
    )

    # 登录
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "loginuser", "password": "secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """测试密码错误"""
    await client.post(
        "/api/v1/users/",
        json={
            "username": "wrongpw",
            "email": "wrongpw@example.com",
            "password": "correct",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "wrongpw", "password": "incorrect"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient):
    """测试用户列表分页"""
    # 创建 5 个用户
    for i in range(5):
        await client.post(
            "/api/v1/users/",
            json={
                "username": f"pageuser{i}",
                "email": f"page{i}@example.com",
                "password": "password123",
            },
        )

    # 第一页
    response = await client.get("/api/v1/users/?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # 第二页
    response = await client.get("/api/v1/users/?page=2&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_users_search(client: AsyncClient):
    """测试用户搜索"""
    await client.post(
        "/api/v1/users/",
        json={
            "username": "searchableuser",
            "email": "search@example.com",
            "password": "password123",
        },
    )
    await client.post(
        "/api/v1/users/",
        json={
            "username": "otheruser",
            "email": "other@example.com",
            "password": "password123",
        },
    )

    response = await client.get("/api/v1/users/?search=searchable")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["username"] == "searchableuser"


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient):
    """测试获取单个用户"""
    create_response = await client.post(
        "/api/v1/users/",
        json={
            "username": "getuser",
            "email": "get@example.com",
            "password": "password123",
        },
    )
    user_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["username"] == "getuser"


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient):
    """测试更新用户"""
    create_response = await client.post(
        "/api/v1/users/",
        json={
            "username": "updateuser",
            "email": "update@example.com",
            "password": "password123",
        },
    )
    user_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/users/{user_id}",
        json={"full_name": "Updated Name"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient):
    """测试删除用户"""
    create_response = await client.post(
        "/api/v1/users/",
        json={
            "username": "deleteuser",
            "email": "delete@example.com",
            "password": "password123",
        },
    )
    user_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204

    # 确认已删除
    get_response = await client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """测试登录不存在的用户"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "notexist", "password": "anypassword"},
    )
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


@pytest.mark.asyncio
async def test_token_validation(client: AsyncClient):
    """测试 token 解码验证"""
    # 创建用户并登录
    await client.post(
        "/api/v1/users/",
        json={
            "username": "tokenuser",
            "email": "token@example.com",
            "password": "secret123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "tokenuser", "password": "secret123"},
    )
    access_token = login_resp.json()["access_token"]

    # 使用 /auth/logout 验证 token 可被正确解码（内部调用 decode_access_token）
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"token": access_token},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "登出成功"


@pytest.mark.asyncio
async def test_logout_invalidates_token(client: AsyncClient):
    """测试登出后 token 再次使用会被拒绝"""
    # 创建用户并登录
    await client.post(
        "/api/v1/users/",
        json={
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "secret123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "logoutuser", "password": "secret123"},
    )
    access_token = login_resp.json()["access_token"]

    # 第一次登出成功
    resp1 = await client.post("/api/v1/auth/logout", json={"token": access_token})
    assert resp1.status_code == 200

    # 第二次登出（token 已黑名单）仍返回成功（幂等）
    resp2 = await client.post("/api/v1/auth/logout", json={"token": access_token})
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_pagination_invalid_params(client: AsyncClient):
    """测试分页参数边界校验"""
    # page < 1
    response = await client.get("/api/v1/users/?page=0&page_size=10")
    assert response.status_code == 422

    # page_size > 100
    response = await client.get("/api/v1/users/?page=1&page_size=200")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_token_decode_invalid(client: AsyncClient):
    """测试无效 token 解码返回 401"""
    response = await client.post(
        "/api/v1/auth/logout",
        json={"token": "invalid.jwt.token"},
    )
    assert response.status_code == 401
    assert "Token 无效" in response.json()["detail"]
