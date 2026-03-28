"""
Webhook 回调 — 任务状态变更时触发 Webhook
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def trigger_webhook_async(
    url: str,
    payload: Dict[str, Any],
    timeout: float = 10.0,
) -> bool:
    """异步触发 Webhook（不阻塞主流程）
    
    Args:
        url: Webhook URL
        payload: 发送的数据
        timeout: 请求超时时间（秒）
    
    Returns:
        bool: 请求是否成功（状态码 2xx）
    """
    if not url:
        return False

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if 200 <= response.status_code < 300:
                logger.info("Webhook 触发成功: %s, status: %d", url, response.status_code)
                return True
            else:
                logger.warning(
                    "Webhook 触发失败: %s, status: %d, body: %s",
                    url, response.status_code, response.text[:200],
                )
                return False
    except Exception as e:
        logger.error("Webhook 请求异常: %s, error: %s", url, e)
        return False


def trigger_webhook_in_background(
    url: str,
    payload: Dict[str, Any],
    background_tasks: Optional["BackgroundTasks"] = None,
) -> None:
    """使用 FastAPI BackgroundTasks 在后台触发 Webhook
    
    这是推荐用法，不阻塞主流程
    """
    if background_tasks:
        from fastapi import BackgroundTasks as FastAPIBackgroundTasks
        if isinstance(background_tasks, FastAPIBackgroundTasks):
            background_tasks.add_task(trigger_webhook_async, url, payload)
    else:
        # 用线程池执行
        asyncio.create_task(trigger_webhook_async(url, payload))


async def notify_task_webhook(
    event_type: str,
    task_id: str,
    task_title: str,
    status: str,
    result: Optional[str] = None,
    error: Optional[str] = None,
    owner_id: Optional[str] = None,
    webhook_url: Optional[str] = None,
    background_tasks: Optional["BackgroundTasks"] = None,
) -> None:
    """任务 Webhook 通知
    
    构建标准 webhook payload 并发送
    """
    url = webhook_url or settings.WEBHOOK_URL
    if not url:
        logger.debug("WEBHOOK_URL 未配置，跳过 webhook 通知")
        return

    payload = {
        "event": event_type,
        "task": {
            "id": task_id,
            "title": task_title,
            "status": status,
            "result": result,
            "error": error,
            "owner_id": owner_id,
        },
    }

    if background_tasks:
        trigger_webhook_in_background(url, payload, background_tasks)
    else:
        await trigger_webhook_async(url, payload)
