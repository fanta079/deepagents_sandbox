"""
Agent Memory - 跨会话记忆存储
"""
from datetime import datetime
from typing import Optional


class AgentMemory:
    def __init__(self):
        self._store: dict[str, list[dict]] = {}  # user_id -> messages

    def add_message(self, user_id: str, role: str, content: str) -> None:
        if user_id not in self._store:
            self._store[user_id] = []
        self._store[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_history(self, user_id: str, limit: int = 50) -> list[dict]:
        messages = self._store.get(user_id, [])
        return messages[-limit:]

    def clear(self, user_id: str) -> None:
        if user_id in self._store:
            del self._store[user_id]

    def search(self, user_id: str, query: str) -> list[dict]:
        """简单关键词匹配"""
        messages = self._store.get(user_id, [])
        return [m for m in messages if query.lower() in m.get("content", "").lower()]


agent_memory = AgentMemory()
