"""
Celery 任务测试 — 验证任务分发和 Celery worker 模拟
"""

import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient


async def create_test_user(client: AsyncClient, username: str) -> str:
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
async def test_dispatch_task_async(client: AsyncClient):
    """测试任务异步分发（Celery 可用时）"""
    user_id = await create_test_user(client, "asyncuser")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "title": "异步任务",
            "owner_id": user_id,
        },
    )
    task_id = create_resp.json()["id"]

    with patch("app.tasks.celery_app.is_celery_available", return_value=True):
        with patch("app.tasks.task_handlers.execute_task.delay") as mock_delay:
            dispatch_resp = await client.post(f"/api/v1/tasks/{task_id}/dispatch")
            assert dispatch_resp.status_code == 200
            data = dispatch_resp.json()
            assert data["mode"] == "async"
            assert data["task_id"] == task_id
            mock_delay.assert_called_once_with(task_id, user_id, "异步任务")


@pytest.mark.asyncio
async def test_dispatch_task_sync_fallback(client: AsyncClient):
    """测试 Celery 不可用时降级为同步执行"""
    user_id = await create_test_user(client, "syncuser")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "title": "同步任务",
            "owner_id": user_id,
        },
    )
    task_id = create_resp.json()["id"]

    with patch("app.tasks.celery_app.is_celery_available", return_value=False):
        dispatch_resp = await client.post(f"/api/v1/tasks/{task_id}/dispatch")
        assert dispatch_resp.status_code == 200
        data = dispatch_resp.json()
        assert data["mode"] == "sync"
        assert data["task_id"] == task_id

    # 验证任务状态变为 success（同步执行）
    get_resp = await client.get(f"/api/v1/tasks/{task_id}")
    task_data = get_resp.json()
    assert task_data["status"] == "success"


@pytest.mark.asyncio
async def test_dispatch_already_running_task_fails(client: AsyncClient):
    """测试只有 pending 状态的任务才能被分发"""
    user_id = await create_test_user(client, "alreadyrunning")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={"title": "已运行任务", "owner_id": user_id},
    )
    task_id = create_resp.json()["id"]

    # 将任务置为 running
    await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "running"},
    )

    dispatch_resp = await client.post(f"/api/v1/tasks/{task_id}/dispatch")
    assert dispatch_resp.status_code == 400
    assert "仅 pending 任务可分发" in dispatch_resp.json()["detail"]


@pytest.mark.asyncio
async def test_dispatch_nonexistent_task(client: AsyncClient):
    """测试分发不存在的任务返回 404"""
    dispatch_resp = await client.post("/api/v1/tasks/nonexistent-id/dispatch")
    assert dispatch_resp.status_code == 404


@pytest.mark.asyncio
async def test_send_email_celery_task():
    """测试 Celery send_email 任务函数"""
    from app.tasks.task_handlers import send_email_task

    with patch("app.tasks.task_handlers.send_email_sync", return_value=True) as mock_send:
        result = send_email_task(to="test@example.com", subject="Test", body="Hello")
        assert result["status"] == "sent"
        assert result["to"] == "test@example.com"
        mock_send.assert_called_once_with(
            to_email="test@example.com",
            subject="Test",
            body="Hello",
        )


@pytest.mark.asyncio
async def test_send_email_celery_task_failure():
    """测试 Celery send_email 任务失败时返回 failed"""
    from app.tasks.task_handlers import send_email_task

    with patch(
        "app.tasks.task_handlers.send_email_sync",
        side_effect=Exception("SMTP error"),
    ):
        result = send_email_task(to="fail@example.com", subject="Test", body="Hello")
        assert result["status"] == "failed"
        assert "SMTP error" in result["error"]


@pytest.mark.asyncio
async def test_is_celery_available_check(monkeypatch):
    """测试 is_celery_available 正确检测 Redis 连接"""
    from app.tasks.celery_app import is_celery_available

    # Mock successful redis ping
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True

    class FakeSettings:
        REDIS_HOST = "localhost"
        REDIS_PORT = 6379
        REDIS_DB = 0
        REDIS_PASSWORD = None

    with patch("redis.Redis", return_value=mock_redis):
        with patch("app.tasks.celery_app.settings", FakeSettings):
            result = is_celery_available()
            assert result is True


@pytest.mark.asyncio
async def test_is_celery_available_redis_down(monkeypatch):
    """测试 Redis 不可用时 is_celery_available 返回 False"""
    from app.tasks.celery_app import is_celery_available

    with patch("redis.Redis", side_effect=Exception("Connection refused")):
        result = is_celery_available()
        assert result is False


@pytest.mark.asyncio
async def test_execute_task_celery_success():
    """测试 execute_task Celery 任务成功执行"""
    from app.tasks.task_handlers import execute_task

    with patch("app.tasks.celery_app.is_celery_available", return_value=True):
        with patch.object(execute_task, "update_state"):
            with patch(
                "app.core.database.AsyncSessionLocal",
            ):
                result = execute_task(
                    task_id="test-task-123",
                    owner_id="test-owner",
                    task_title="Test Task",
                )
                assert result["status"] == "success"
                assert result["task_id"] == "test-task-123"


@pytest.mark.asyncio
async def test_dispatch_does_not_change_other_fields(client: AsyncClient):
    """测试 dispatch 不影响任务的其他字段（仅改变状态）"""
    user_id = await create_test_user(client, "dispatchfields")

    create_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "title": "字段测试任务",
            "owner_id": user_id,
            "priority": "high",
            "tags": ["test"],
        },
    )
    task_id = create_resp.json()["id"]

    with patch("app.tasks.celery_app.is_celery_available", return_value=False):
        await client.post(f"/api/v1/tasks/{task_id}/dispatch")

    get_resp = await client.get(f"/api/v1/tasks/{task_id}")
    data = get_resp.json()
    assert data["title"] == "字段测试任务"
    assert data["priority"] == "high"
    assert data["tags"] == ["test"]
