"""
DeepAgents - A lightweight agent wrapper for LangChain runnables.

Provides create_deep_agent() factory for building agent chains with
a model, system prompt, and optional tool/sandbox backend.
"""

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableSerializable


class DeepAgent(RunnableSerializable):
    """
    Simple agent wrapper that pipes system prompt + messages into a model.

    invoke({"messages": [...]}) → AIMessage
    """

    def __init__(self, model, system_prompt: str, backend=None):
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_core.runnables import RunnablePassthrough

        self.model = model
        self.backend = backend

        # Build prompt: system + chat history + new messages
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages", optional=True),
        ])

        # Simple chain: prompt → model
        self.chain = prompt | model

    def invoke(self, input_dict, **kwargs):
        if isinstance(input_dict, list):
            input_dict = {"messages": input_dict}
        return self.chain.invoke(input_dict, **kwargs)

    async def ainvoke(self, input_dict, **kwargs):
        if isinstance(input_dict, list):
            input_dict = {"messages": input_dict}
        return await self.chain.ainvoke(input_dict, **kwargs)


def create_deep_agent(model, system_prompt: str, backend=None, **kwargs) -> DeepAgent:
    """
    Factory: create a DeepAgent from a LangChain model, system prompt, and backend.

    Args:
        model: A LangChain chat model (e.g., ChatAnthropic).
        system_prompt: System instruction string.
        backend: Optional sandbox/backend (passed through but not used in this stub).
        **kwargs: Extra kwargs passed to DeepAgent constructor.

    Returns:
        DeepAgent instance (RunnableSerializable).
    """
    return DeepAgent(model=model, system_prompt=system_prompt, backend=backend, **kwargs)
