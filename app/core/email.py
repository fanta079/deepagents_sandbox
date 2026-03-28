"""
邮件通知 — 使用 SMTP 发送邮件（配置化）
"""

import asyncio
import logging
from typing import Optional

from fastapi import BackgroundTasks

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email_sync(
    to_email: str,
    subject: str,
    body: str,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None,
    from_email: Optional[str] = None,
) -> bool:
    """同步发送邮件（实际 SMTP 发送）
    
    Returns:
        bool: 发送是否成功
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    host = smtp_host or settings.SMTP_HOST
    port = smtp_port or settings.SMTP_PORT
    user = smtp_user or settings.SMTP_USER
    password = smtp_password or settings.SMTP_PASSWORD
    sender = from_email or settings.SMTP_FROM

    if not host or not user or not password:
        logger.warning("SMTP 未完整配置，跳过邮件发送: %s -> %s", sender, to_email)
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        logger.info("邮件发送成功: %s -> %s", sender, to_email)
        return True
    except Exception as e:
        logger.error("邮件发送失败: %s -> %s, error: %s", sender, to_email, e)
        return False


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    background_tasks: Optional[BackgroundTasks] = None,
) -> bool:
    """发送邮件（异步，异步不阻塞主流程）
    
    Args:
        to_email: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文
        background_tasks: FastAPI BackgroundTasks（若传入则在后台发送）
    """
    if background_tasks:
        background_tasks.add_task(
            send_email_sync,
            to_email=to_email,
            subject=subject,
            body=body,
        )
        return True
    else:
        # 无 BackgroundTasks 时，用线程池异步执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, send_email_sync, to_email, subject, body
        )


async def notify_task_status_change(
    task_title: str,
    task_id: str,
    old_status: str,
    new_status: str,
    user_email: str,
    background_tasks: Optional[BackgroundTasks] = None,
) -> None:
    """任务状态变更邮件通知
    
    当任务完成（success/failed）时，通知用户
    """
    if new_status in ("success", "failed"):
        subject = f"[任务通知] {task_title} - {new_status.upper()}"
        body = (
            f"任务状态变更通知\n\n"
            f"任务: {task_title}\n"
            f"任务 ID: {task_id}\n"
            f"状态变更: {old_status} -> {new_status}\n\n"
            f"详情请访问系统查看。"
        )
        await send_email(
            to_email=user_email,
            subject=subject,
            body=body,
            background_tasks=background_tasks,
        )
