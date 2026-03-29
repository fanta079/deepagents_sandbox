"""
LangSmith 集成 - LLM 调用追踪（可选功能）

启用方式：
    LANGCHAIN_TRACING=true
    LANGCHAIN_API_KEY=your_api_key
    LANGCHAIN_PROJECT=deepagents  # 可选，默认为 deepagents

对接 DeerFlow 的 LangSmith 追踪能力，提升 AI Agent 的可观测性。
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ——— 配置读取 ————————————————————————————————————————————————————

LANGCHAIN_TRACING: bool = os.getenv("LANGCHAIN_TRACING", "false").lower() == "true"
LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "deepagents")
LANGCHAIN_ENDPOINT: str = os.getenv(
    "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
)
LANGCHAIN_API_KEY: Optional[str] = os.getenv("LANGCHAIN_API_KEY", "") or None


def setup_langsmith() -> bool:
    """
    初始化 LangSmith 追踪。

    仅当 LANGCHAIN_TRACING=true 且 LANGCHAIN_API_KEY 有效时生效。
    通过环境变量配置，deer-flow 用户可直接复用相同配置。

    Returns:
        True 表示成功启用，None 表示未启用
    """
    if not LANGCHAIN_TRACING:
        logger.info("LangSmith 追踪未启用（LANGCHAIN_TRACING=false）")
        return False

    if not LANGCHAIN_API_KEY:
        logger.warning("LangSmith API Key 未配置（LANGCHAIN_API_KEY），跳过启用")
        return False

    try:
        # 设置 LangChain v2 追踪环境变量
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = LANGCHAIN_ENDPOINT
        os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY

        # 尝试导入 langchain_core 并设置回调
        try:
            from langchain_core.callbacks import LangChainCallbackHandler
            from langchain_core.tracers.langchain import LangChainTracer

            tracer = LangChainTracer(
                project_name=LANGCHAIN_PROJECT,
                endpoint=LANGCHAIN_ENDPOINT,
            )
            logger.info(
                f"✅ LangSmith 追踪已启用，项目：{LANGCHAIN_PROJECT}，端点：{LANGCHAIN_ENDPOINT}"
            )
            return True
        except ImportError:
            logger.info(
                f"✅ LangSmith 环境变量已设置（项目：{LANGCHAIN_PROJECT}），"
                "LangChain 回调将在实际调用时自动生效"
            )
            return True

    except Exception as e:
        logger.warning(f"⚠️ LangSmith 初始化失败（{e}），跳过启用")
        return False


def get_langsmith_callbacks():
    """
    获取 LangSmith 回调处理器列表。

    可在 LLM 调用时传入，用于追踪具体请求。
    """
    if not LANGCHAIN_TRACING or not LANGCHAIN_API_KEY:
        return []

    try:
        from langchain_core.callbacks import LangChainCallbackHandler
        return [LangChainCallbackHandler()]
    except ImportError:
        return []
