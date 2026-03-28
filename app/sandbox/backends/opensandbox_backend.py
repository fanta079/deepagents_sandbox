"""
OpenSandbox Backend for DeepAgents

实现 DeepAgents 的 SandboxBackend 接口，接入阿里云 OpenSandbox
文档: https://open-sandbox.ai/
"""

import asyncio
import os
import uuid
from datetime import timedelta
from typing import Optional, AsyncIterator

from dotenv import load_dotenv

try:
    from opensandbox import Sandbox, SandboxSync
    from opensandbox.config import ConnectionConfig, ConnectionConfigSync
    from opensandbox.models import WriteEntry
except ImportError:
    raise ImportError(
        "OpenSandbox SDK not installed. Run: pip install opensandbox"
    )

from deepagents.backends.sandbox import SandboxBackend

load_dotenv()


class OpenSandboxBackend(SandboxBackend):
    """
    OpenSandbox 沙箱后端

    支持两种模式:
    1. 云服务模式: 连接到 api.opensandbox.io
    2. 自部署模式: 连接到私有 OpenSandbox Server

    环境变量:
    - OPENSANDBOX_DOMAIN: 服务器地址 (默认: api.opensandbox.io)
    - OPENSANDBOX_API_KEY: API Key
    - OPENSANDBOX_IMAGE: 沙箱镜像 (默认: ubuntu)
    """

    def __init__(
        self,
        image: str = None,
        domain: str = None,
        api_key: str = None,
        timeout: timedelta = None,
    ):
        self.image = image or os.getenv("OPENSANDBOX_IMAGE", "ubuntu")
        self.domain = domain or os.getenv("OPENSANDBOX_DOMAIN", "api.opensandbox.io")
        self.api_key = api_key or os.getenv("OPENSANDBOX_API_KEY", "")
        self.timeout = timeout or timedelta(minutes=30)

        self._sandbox: Optional[Sandbox] = None
        self._sandbox_id: Optional[str] = None

    async def _get_sandbox(self) -> Sandbox:
        """获取或创建沙箱实例（懒加载/冷启动）"""
        if self._sandbox is None:
            config = ConnectionConfig(
                domain=self.domain,
                api_key=self.api_key,
            )
            self._sandbox = await Sandbox.create(
                self.image,
                connection_config=config,
                timeout=self.timeout,
            )
            self._sandbox_id = self._sandbox.id
        return self._sandbox

    async def execute(self, command: str) -> str:
        """
        在沙箱中执行 shell 命令

        对应 DeepAgents 的 execute 工具
        """
        sandbox = await self._get_sandbox()
        execution = await sandbox.commands.run(command)
        return execution.logs.stdout[0].text if execution.logs.stdout else ""

    async def read_file(self, path: str) -> bytes:
        """读取沙箱内文件"""
        sandbox = await self._get_sandbox()
        content = await sandbox.files.read_file(path)
        if isinstance(content, str):
            return content.encode("utf-8")
        return content

    async def write_file(self, path: str, content: bytes) -> None:
        """写入沙箱内文件"""
        sandbox = await self._get_sandbox()
        data = content.decode("utf-8") if isinstance(content, bytes) else content
        await sandbox.files.write_files([
            WriteEntry(path=path, data=data, mode=644)
        ])

    async def ls(self, path: str = ".") -> list[str]:
        """列出沙箱内目录"""
        sandbox = await self._get_sandbox()
        result = await sandbox.commands.run(f"ls -la {path}")
        lines = result.logs.stdout[0].text.split("\n") if result.logs.stdout else []
        return [line.split()[-1] for line in lines if line and line.split()[-1] not in [".", ".."]]

    async def glob(self, pattern: str) -> list[str]:
        """沙箱内 glob"""
        sandbox = await self._get_sandbox()
        result = await sandbox.commands.run(f"find . -name '{pattern}'")
        return [
            line.strip()
            for line in (result.logs.stdout[0].text.split("\n") if result.logs.stdout else [])
            if line.strip()
        ]

    async def grep(self, pattern: str, path: str = ".") -> list[str]:
        """沙箱内 grep"""
        sandbox = await self._get_sandbox()
        result = await sandbox.commands.run(f"grep -r '{pattern}' {path}")
        return [
            line.strip()
            for line in (result.logs.stdout[0].text.split("\n") if result.logs.stdout else [])
            if line.strip()
        ]

    async def rm(self, path: str) -> None:
        """删除沙箱内文件"""
        sandbox = await self._get_sandbox()
        await sandbox.commands.run(f"rm -rf {path}")

    async def kill(self) -> None:
        """销毁沙箱"""
        if self._sandbox:
            await self._sandbox.kill()
            self._sandbox = None
            self._sandbox_id = None

    async def pause(self) -> None:
        """暂停沙箱"""
        sandbox = await self._get_sandbox()
        await sandbox.pause()

    async def resume(self) -> None:
        """恢复沙箱"""
        if self._sandbox_id:
            config = ConnectionConfig(domain=self.domain, api_key=self.api_key)
            self._sandbox = await Sandbox.resume(self._sandbox_id, connection_config=config)

    async def renew(self, duration: timedelta) -> None:
        """续期沙箱"""
        sandbox = await self._get_sandbox()
        await sandbox.renew(duration)


class OpenSandboxBackendPool:
    """
    OpenSandbox 沙箱池（用于高频场景）

    维护预热的沙箱实例池，减少冷启动延迟
    """

    def __init__(
        self,
        image: str = None,
        domain: str = None,
        api_key: str = None,
        pool_size: int = 2,
        timeout: timedelta = timedelta(minutes=30),
    ):
        self.image = image or os.getenv("OPENSANDBOX_IMAGE", "ubuntu")
        self.domain = domain or os.getenv("OPENSANDBOX_DOMAIN", "api.opensandbox.io")
        self.api_key = api_key or os.getenv("OPENSANDBOX_API_KEY", "")
        self.pool_size = pool_size
        self.timeout = timeout

        self._pool: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self):
        """初始化沙箱池（预热）"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            config = ConnectionConfig(domain=self.domain, api_key=self.api_key)
            for _ in range(self.pool_size):
                sandbox = await Sandbox.create(
                    self.image,
                    connection_config=config,
                    timeout=self.timeout,
                )
                await self._pool.put(sandbox)

            self._initialized = True

    async def acquire(self) -> Sandbox:
        """从池中获取沙箱"""
        await self.initialize()

        try:
            return self._pool.get_nowait()
        except asyncio.QueueEmpty:
            # 池空时创建新的
            config = ConnectionConfig(domain=self.domain, api_key=self.api_key)
            return await Sandbox.create(
                self.image,
                connection_config=config,
                timeout=self.timeout,
            )

    async def release(self, sandbox: Sandbox):
        """归还沙箱到池中"""
        try:
            self._pool.put_nowait(sandbox)
        except asyncio.QueueFull:
            await sandbox.kill()

    async def shutdown(self):
        """关闭池，清理所有沙箱"""
        while not self._pool.empty():
            try:
                sandbox = self._pool.get_nowait()
                await sandbox.kill()
            except asyncio.QueueEmpty:
                break
        self._initialized = False
