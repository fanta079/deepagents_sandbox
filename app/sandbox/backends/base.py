"""
Sandbox Backend 统一接口定义
"""
from abc import ABC, abstractmethod
from typing import Any


class SandboxBackend(ABC):
    """沙箱后端统一抽象接口"""

    @abstractmethod
    async def initialize(self) -> None:
        """初始化沙箱实例"""
        ...

    @abstractmethod
    async def execute(self, code: str, **kwargs) -> dict[str, Any]:
        """执行代码或命令"""
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """清理沙箱资源"""
        ...
