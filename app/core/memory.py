"""
Memory utilities - 无状态设计，所有上下文由调用方管理

注意：本模块不存储任何用户上下文，仅提供临时工具函数
"""
from datetime import datetime
from typing import Any


def build_context(messages: list[dict], system_prompt: str | None = None) -> list[dict]:
    """
    从消息列表构建上下文（调用方传入，无状态）
    
    Args:
        messages: 消息列表 [{"role": "user", "content": "..."}]
        system_prompt: 系统提示词
    
    Returns:
        构建好的消息列表
    """
    context = []
    if system_prompt:
        context.append({"role": "system", "content": system_prompt})
    context.extend(messages)
    return context


def estimate_tokens(text: str) -> int:
    """
    估算 token 数量（粗略估算，中文≈2token/字，英文≈4token/词）
    """
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    english_words = sum(1 for w in text.split() if w.isascii())
    other = len(text) - chinese_chars - sum(1 for c in english_words if c.isascii())
    return int(chinese_chars * 1.5 + english_words * 0.25 + other * 1)


def trim_messages(messages: list[dict], max_tokens: int = 4000) -> list[dict]:
    """
    裁剪消息列表，确保总 token 数不超过限制（无状态操作）
    
    Args:
        messages: 消息列表
        max_tokens: 最大 token 数
    
    Returns:
        裁剪后的消息列表
    """
    if not messages:
        return []
    
    total = sum(estimate_tokens(m.get("content", "")) for m in messages)
    if total <= max_tokens:
        return messages
    
    # 从旧到新保留
    result = []
    running_total = 0
    for msg in reversed(messages):
        tokens = estimate_tokens(msg.get("content", ""))
        if running_total + tokens > max_tokens:
            break
        result.insert(0, msg)
        running_total += tokens
    
    return result


class AgentMemory:
    """In-memory agent context storage (per-user message history)."""

    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    def add_message(self, user_id: str, role: str, content: str) -> None:
        if user_id not in self._store:
            self._store[user_id] = []
        self._store[user_id].append({"role": role, "content": content})

    def get_history(self, user_id: str, limit: int | None = None) -> list[dict]:
        history = self._store.get(user_id, [])
        if limit:
            return history[-limit:]
        return history

    def get_context_count(self, user_id: str) -> int:
        return len(self._store.get(user_id, []))

    def clear(self, user_id: str) -> None:
        self._store.pop(user_id, None)

    def trim_context(self, user_id: str, keep_last: int) -> int:
        if user_id not in self._store:
            return 0
        msgs = self._store[user_id]
        removed = len(msgs) - keep_last
        if removed > 0:
            self._store[user_id] = msgs[-keep_last:]
        else:
            self._store[user_id] = msgs
        return max(removed, 0)


agent_memory = AgentMemory()
