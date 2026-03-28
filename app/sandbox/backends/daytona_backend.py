"""
Daytona 沙箱后端框架

占位实现，尚未接入真实 Daytona SDK。
文档: https://www.daytona.io/
"""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Optional

# from daytona import Daytona
# from langchain_daytona import DaytonaSandbox


class DaytonaBackendPlaceholder:
    """
    Daytona 后端占位符

    接入步骤:
    1. pip install daytona langchain-daytona
    2. 设置 DAYTONA_API_KEY 环境变量
    3. 取消下面注释并完善初始化逻辑
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "ubuntu",
        timeout: timedelta = timedelta(minutes=30),
    ):
        self.api_key = api_key or os.getenv("DAYTONA_API_KEY", "")
        self.model = model
        self.timeout = timeout
        self._sandbox = None

    async def initialize(self):
        """初始化 Daytona 沙箱连接"""
        # daytona = Daytona(api_key=self.api_key)
        # self._sandbox = daytona.create(model=self.model)
        raise NotImplementedError("Daytona 后端尚未接入，请联系开发者")

    async def execute(self, command: str) -> str:
        raise NotImplementedError("Daytona 后端尚未接入")

    async def kill(self):
        if self._sandbox:
            # await self._sandbox.kill()
            self._sandbox = None
