"""
任务 API 测试
"""

import pytest
from httpx import AsyncClient


async def create_test_user(client: AsyncClient, username: str = "taskuser") -> str:
    """辅助函数：创建测试用户并返回 user_id"""
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "password123",
        },
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    """测试创建任务"""
    user_id = await create_test_user(client, "taskuser1")

    response = await client.post(
        "/api/v1/tasks/",
        json={
            "title": "测试任务",
            "description": "这是一个测试任务",
            "priority": "high",
            "owner_id": user_id,
            "max_retries": 3,
            "tags": ["test", "demo"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "测试任务"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert data["tags"] == ["test", "demo"]


@pytest.mark.asyncio
async def test_create_task_invalid_owner(client: AsyncClient):
    """测试创建任务时指定不存在的 owner"""
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "title": "无效任务",
            "owner_id": "non-existent-user-id",
        },
    )
    assert response.status_code == 404
    assert "所属用户不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_tasks_pagination(client: AsyncClient):
    """测试任务列表分页"""
    user_id = await create_test_user(client, "pagetask")

    # 创建 5 个任务
    for i in range(5):
        await client.post(
            "/api/v1/tasks/",
            json={
                "title": f"分页任务{i}",
                "owner_id": user_id,
            },
        )

    response = await client.get("/api/v1/tasks/?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(client: AsyncClient):
    """测试按状态过滤任务"""
    user_id = await create_test_user(client, "filtertask")

    # 创建任务
    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "待处理任务", "owner_id": user_id},
    )
    task_id = create_resp.json()["id"]

    # 将任务状态更新为 running
    await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "running"},
    )

    # 过滤 running 任务
    response = await client.get("/api/v1/tasks/?status=running")
    assert response.status_code == 200
    data = response.json()
    assert all(t["status"] == "running" for t in data)


@pytest.mark.asyncio
async def test_list_tasks_search(client: AsyncClient):
    """测试任务搜索"""
    user_id = await create_test_user(client, "searchtask")

    await client.post(
        "/api/v1/tasks/",
        json={"title": "搜索关键词任务", "owner_id": user_id},
    )
    await client.post(
        "/api/v1/tasks/",
        json={"title": "其他任务", "owner_id": user_id},
    )

    response = await client.get("/api/v1/tasks/?search=关键词")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("关键词" in t["title"] for t in data)


@pytest.mark.asyncio
async def test_update_task_status(client: AsyncClient):
    """测试更新任务状态"""
    user_id = await create_test_user(client, "statustask")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "状态更新任务", "owner_id": user_id},
    )
    task_id = create_resp.json()["id"]

    # pending -> running
    response = await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "running", "progress": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["progress"] == 10
    assert data["started_at"] is not None

    # running -> success
    response = await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "success", "result": "完成"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"] == "完成"
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_retry_failed_task(client: AsyncClient):
    """测试重试失败任务"""
    user_id = await create_test_user(client, "retrytask")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "失败任务", "owner_id": user_id, "max_retries": 3},
    )
    task_id = create_resp.json()["id"]

    # 将任务标记为失败
    await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "failed", "error": "Something went wrong"},
    )

    # 重试
    response = await client.patch(f"/api/v1/tasks/{task_id}/retry")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["retry_count"] == 1
    assert data["error"] is None


@pytest.mark.asyncio
async def test_retry_non_failed_task(client: AsyncClient):
    """测试只有失败任务才能重试"""
    user_id = await create_test_user(client, "notfailed")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "非失败任务", "owner_id": user_id},
    )
    task_id = create_resp.json()["id"]

    response = await client.patch(f"/api/v1/tasks/{task_id}/retry")
    assert response.status_code == 400
    assert "只有失败任务可以重试" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_task(client: AsyncClient):
    """测试取消任务"""
    user_id = await create_test_user(client, "canceltask")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "可取消任务", "owner_id": user_id},
    )
    task_id = create_resp.json()["id"]

    response = await client.post(f"/api/v1/tasks/{task_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient):
    """测试删除任务"""
    user_id = await create_test_user(client, "deltask")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "待删除任务", "owner_id": user_id},
    )
    task_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204

    # 确认已删除
    get_resp = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_running_task_fails(client: AsyncClient):
    """测试删除运行中的任务会失败"""
    user_id = await create_test_user(client, "delrunning")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "运行中任务", "owner_id": user_id},
    )
    task_id = create_resp.json()["id"]

    # 先将其置为 running
    await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "running"},
    )

    response = await client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 400
    assert "正在运行，无法删除" in response.json()["detail"]


@pytest.mark.asyncio
async def test_status_transition_invalid(client: AsyncClient):
    """测试非法状态流转被拒绝"""
    user_id = await create_test_user(client, "invalidtrans")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "非法流转任务", "owner_id": user_id},
    )
    task_id = create_resp.json()["id"]

    # pending -> success 直接流转（非法，必须经过 running）
    response = await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "success", "result": "作弊"},
    )
    assert response.status_code == 400
    assert "非法状态流转" in response.json()["detail"]


@pytest.mark.asyncio
async def test_retry_max_retries_exceeded(client: AsyncClient):
    """测试达到最大重试次数后无法再重试"""
    user_id = await create_test_user(client, "maxretry")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "已达上限任务", "owner_id": user_id, "max_retries": 1},
    )
    task_id = create_resp.json()["id"]

    # 第一次失败
    await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "failed", "error": "Error 1"},
    )
    # 第一次重试成功
    retry1 = await client.patch(f"/api/v1/tasks/{task_id}/retry")
    assert retry1.json()["retry_count"] == 1

    # 第二次失败
    await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "failed", "error": "Error 2"},
    )
    # 第二次重试应该失败（已达 max_retries=1）
    response = await client.patch(f"/api/v1/tasks/{task_id}/retry")
    assert response.status_code == 400
    assert "最大重试次数" in response.json()["detail"]


@pytest.mark.asyncio
async def test_retry_resets_task_state(client: AsyncClient):
    """测试重试后任务状态正确重置"""
    user_id = await create_test_user(client, "retryreset")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "重置测试任务", "owner_id": user_id, "max_retries": 2},
    )
    task_id = create_resp.json()["id"]

    # 运行并失败
    await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "running", "progress": 50},
    )
    await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "failed", "error": "Some error"},
    )

    # 重试
    retry_resp = await client.patch(f"/api/v1/tasks/{task_id}/retry")
    data = retry_resp.json()
    assert data["status"] == "pending"
    assert data["retry_count"] == 1
    assert data["error"] is None
    assert data["progress"] == 0
    assert data["started_at"] is None
    assert data["completed_at"] is None


@pytest.mark.asyncio
async def test_cancel_running_task(client: AsyncClient):
    """测试取消运行中的任务"""
    user_id = await create_test_user(client, "cancelrunning")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "运行中取消任务", "owner_id": user_id},
    )
    task_id = create_resp.json()["id"]

    # 先运行
    await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "running"},
    )

    # 取消
    cancel_resp = await client.post(f"/api/v1/tasks/{task_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"
