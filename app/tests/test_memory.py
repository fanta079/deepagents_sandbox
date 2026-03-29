"""
单元测试 — app/core/memory.py
"""
import pytest
from app.core.memory import AgentMemory, agent_memory


class TestAgentMemory:
    """AgentMemory 单元测试"""

    def setup_method(self):
        """每个测试前创建新实例"""
        self.memory = AgentMemory()

    def test_add_message_single(self):
        """测试添加单条消息"""
        self.memory.add_message("user1", "user", "Hello")
        history = self.memory.get_history("user1")
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert "timestamp" in history[0]

    def test_add_message_multiple(self):
        """测试添加多条消息"""
        self.memory.add_message("user1", "user", "Hello")
        self.memory.add_message("user1", "assistant", "Hi there")
        self.memory.add_message("user1", "user", "How are you?")
        history = self.memory.get_history("user1")
        assert len(history) == 3

    def test_get_history_limit(self):
        """测试历史记录限制"""
        for i in range(60):
            self.memory.add_message("user1", "user", f"Message {i}")
        history = self.memory.get_history("user1", limit=10)
        assert len(history) == 10
        assert history[0]["content"] == "Message 50"

    def test_get_history_no_user(self):
        """测试不存在的用户返回空列表"""
        history = self.memory.get_history("nonexistent")
        assert history == []

    def test_clear_user(self):
        """测试清除用户历史"""
        self.memory.add_message("user1", "user", "Hello")
        self.memory.add_message("user2", "user", "World")
        self.memory.clear("user1")
        assert self.memory.get_history("user1") == []
        assert len(self.memory.get_history("user2")) == 1

    def test_clear_nonexistent(self):
        """测试清除不存在的用户不抛异常"""
        self.memory.clear("nonexistent")  # 不应抛异常

    def test_search_found(self):
        """测试关键词搜索 — 找到"""
        self.memory.add_message("user1", "user", "What is Python?")
        self.memory.add_message("user1", "assistant", "Python is a programming language.")
        self.memory.add_message("user1", "user", "Tell me about Java")
        results = self.memory.search("user1", "Python")
        assert len(results) == 2

    def test_search_case_insensitive(self):
        """测试搜索大小写不敏感"""
        self.memory.add_message("user1", "user", "Hello WORLD")
        results = self.memory.search("user1", "hello")
        assert len(results) == 1

    def test_search_not_found(self):
        """测试关键词搜索 — 未找到"""
        self.memory.add_message("user1", "user", "Hello")
        results = self.memory.search("user1", "goodbye")
        assert results == []

    def test_search_no_user(self):
        """测试搜索不存在的用户返回空"""
        results = self.memory.search("nonexistent", "hello")
        assert results == []

    def test_timestamp_added(self):
        """测试每条消息都包含时间戳"""
        self.memory.add_message("user1", "user", "Hello")
        history = self.memory.get_history("user1")
        assert "timestamp" in history[0]
        assert history[0]["timestamp"] is not None

    def test_multiple_users_isolated(self):
        """测试不同用户记忆隔离"""
        self.memory.add_message("user1", "user", "User1 message")
        self.memory.add_message("user2", "user", "User2 message")
        u1_history = self.memory.get_history("user1")
        u2_history = self.memory.get_history("user2")
        assert u1_history[0]["content"] == "User1 message"
        assert u2_history[0]["content"] == "User2 message"


class TestAgentMemorySingleton:
    """测试 agent_memory 单例"""

    def test_singleton_basic(self):
        """测试单例可添加消息"""
        agent_memory.add_message("test_user", "user", "Singleton test")
        history = agent_memory.get_history("test_user")
        assert len(history) >= 1
        # 清理
        agent_memory.clear("test_user")
