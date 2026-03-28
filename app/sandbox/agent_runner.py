"""
DeepAgents 沙箱集成模块

支持多种沙箱后端:
- Daytona (langchain-daytona)
- OpenSandbox (opensandbox)
- Modal (langchain-modal)
- 自定义后端
"""

import os
import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Optional

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from deepagents import create_deep_agent

load_dotenv()


class SandboxAgent:
    """带沙箱的 DeepAgent，支持多种后端"""

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-20250514",
        system_prompt: str = "You are a helpful coding assistant with sandbox access.",
        backend_type: str = "opensandbox",  # opensandbox, daytona, modal
    ):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.backend_type = backend_type
        self.backend = None
        self.agent = None

    def _create_backend(self):
        """根据 backend_type 创建对应的沙箱后端"""
        if self.backend_type == "opensandbox":
            from app.sandbox.backends.opensandbox_backend import OpenSandboxBackend

            return OpenSandboxBackend(
                image=os.getenv("OPENSANDBOX_IMAGE", "ubuntu"),
                domain=os.getenv("OPENSANDBOX_DOMAIN", "api.opensandbox.io"),
                api_key=os.getenv("OPENSANDBOX_API_KEY", ""),
                timeout=timedelta(minutes=30),
            )

        elif self.backend_type == "daytona":
            from daytona import Daytona
            from langchain_daytona import DaytonaSandbox

            daytona = Daytona()
            sandbox = daytona.create()
            return DaytonaSandbox(sandbox=sandbox)

        elif self.backend_type == "modal":
            import modal
            from langchain_modal import ModalSandbox

            app = modal.App.lookup(os.getenv("MODAL_APP_NAME", "your-app"))
            modal_sandbox = modal.Sandbox.create(app=app)
            return ModalSandbox(sandbox=modal_sandbox)

        else:
            raise ValueError(f"Unknown backend type: {self.backend_type}")

    def _create_model(self):
        """创建 LLM 模型"""
        return ChatAnthropic(model=self.model_name)

    async def initialize(self):
        """初始化 Agent 和沙箱（冷启动）"""
        backend = self._create_backend()
        model = self._create_model()

        self.backend = backend
        self.agent = create_deep_agent(
            model=model,
            system_prompt=self.system_prompt,
            backend=backend,
        )
        return self

    async def invoke(self, messages: list):
        """调用 Agent 处理请求"""
        if self.agent is None:
            await self.initialize()

        result = self.agent.invoke({"messages": messages})
        return result

    async def stop(self):
        """停止沙箱"""
        if hasattr(self.backend, "kill"):
            await self.backend.kill()
        self.backend = None
        self.agent = None


# 全局单例（可选）
_agent_instance: Optional[SandboxAgent] = None


async def get_agent(backend_type: str = "opensandbox") -> SandboxAgent:
    """获取或创建 Agent 实例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = SandboxAgent(backend_type=backend_type)
        await _agent_instance.initialize()
    return _agent_instance


async def shutdown_agent():
    """关闭 Agent 和沙箱"""
    global _agent_instance
    if _agent_instance:
        await _agent_instance.stop()
        _agent_instance = None
