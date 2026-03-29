"""
多 Agent 协作编排器 - 基于 LangGraph

支持：
- 单一 Agent 调用
- 多个 Agent 串行协作（一个 Agent 输出作为下一个输入）
- 多个 Agent 并行协作（一个任务分发多个 Agent，结果汇总）
"""
import asyncio
from typing import Any, TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


def add_messages(left: Sequence[BaseMessage], right: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    """合并消息列表"""
    return list(left) + list(right)


class AgentState(TypedDict):
    """Agent 状态"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: str | None
    results: dict[str, Any]


class MultiAgentOrchestrator:
    """多 Agent 编排器"""

    def __init__(self):
        self.agents: dict[str, Any] = {}
        self.graph = None

    def register_agent(self, name: str, agent_func):
        """注册 Agent"""
        self.agents[name] = agent_func

    async def invoke_single(self, agent_name: str, input_text: str) -> str:
        """单一 Agent 调用"""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        return await self.agents[agent_name](input_text)

    async def invoke_sequential(self, agent_sequence: list[str], input_text: str) -> str:
        """串行协作：结果逐个传递"""
        current_input = input_text
        for agent_name in agent_sequence:
            current_input = await self.invoke_single(agent_name, current_input)
        return current_input

    async def invoke_parallel(self, agent_names: list[str], input_text: str) -> dict[str, str]:
        """并行协作：同时调用，结果汇总"""
        tasks = [self.invoke_single(name, input_text) for name in agent_names]
        results = await asyncio.gather(*tasks)
        return dict(zip(agent_names, results))

    async def invoke_dag(self, dag_definition: dict[str, list[str]], input_text: str) -> dict[str, str]:
        """
        DAG 协作：支持更复杂的依赖关系
        dag_definition: {"agent_a": [], "agent_b": ["agent_a"], "agent_c": ["agent_a"]}
        """
        results = {}
        executed = set()

        async def execute_with_deps(agent_name: str):
            deps = dag_definition.get(agent_name, [])
            for dep in deps:
                if dep not in executed:
                    await execute_with_deps(dep)
            results[agent_name] = await self.invoke_single(agent_name, input_text)
            executed.add(agent_name)

        # 找根节点（无依赖）
        roots = [name for name, deps in dag_definition.items() if not deps]
        for root in roots:
            await execute_with_deps(root)

        return results


orchestrator = MultiAgentOrchestrator()
