"""
Modal 沙箱后端框架

占位实现，尚未接入真实 Modal SDK。
文档: https://modal.com/
"""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Optional


class ModalBackendPlaceholder:
    """
    Modal 后端占位符

    接入步骤:
    1. pip install modal
    2. 设置 MODAL_TOKEN_ID / MODAL_TOKEN_SECRET 环境变量
    3. 取消下面注释并完善初始化逻辑
    """

    def __init__(
        self,
        app_name: Optional[str] = None,
        image: str = "python:3.11",
        timeout: timedelta = timedelta(minutes=30),
    ):
        self.app_name = app_name or os.getenv("MODAL_APP_NAME", "deepagent")
        self.image = image
        self.timeout = timeout
        self._sandbox = None

    async def initialize(self):
        """初始化 Modal 沙箱连接"""
        # import modal
        # self._app = modal.App.lookup(self.app_name)
        # self._sandbox = await modal.Sandbox.create(app=self._app)
        raise NotImplementedError("Modal 后端尚未接入，请联系开发者")

    async def execute(self, command: str) -> str:
        raise NotImplementedError("Modal 后端尚未接入")

    async def kill(self):
        if self._sandbox:
            # await self._sandbox.kill()
            self._sandbox = None
