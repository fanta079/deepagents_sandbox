"""
单元测试 — app/core/memory.py (无状态设计)
"""
import pytest
from app.core.memory import build_context, estimate_tokens, trim_messages, AgentMemory, agent_memory


class TestBuildContext:
    """测试上下文构建"""

    def test_build_context_empty(self):
        """测试空消息"""
        result = build_context([])
        assert result == []

    def test_build_context_with_messages(self):
        """测试带消息的上下文"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        result = build_context(messages)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_build_context_with_system_prompt(self):
        """测试带系统提示词"""
        messages = [{"role": "user", "content": "Hello"}]
        result = build_context(messages, system_prompt="You are a helpful assistant")
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are a helpful assistant"

    def test_build_context_no_system(self):
        """测试无系统提示词时不添加"""
        messages = [{"role": "user", "content": "Hello"}]
        result = build_context(messages, system_prompt=None)
        assert len(result) == 1


class TestEstimateTokens:
    """测试 token 估算"""

    def test_estimate_empty(self):
        """测试空字符串"""
        assert estimate_tokens("") == 0

    def test_estimate_english(self):
        """测试英文"""
        text = "Hello world"
        result = estimate_tokens(text)
        assert result > 0

    def test_estimate_chinese(self):
        """测试中文"""
        text = "你好世界"
        result = estimate_tokens(text)
        assert result > 0

    def test_estimate_mixed(self):
        """测试中英混合"""
        text = "Hello 你好 world 世界"
        result = estimate_tokens(text)
        assert result > 0


class TestTrimMessages:
    """测试消息裁剪（无状态）"""

    def test_trim_empty(self):
        """测试空消息"""
        result = trim_messages([])
        assert result == []

    def test_trim_under_limit(self):
        """测试未超过限制"""
        messages = [
            {"role": "user", "content": "Short"},
            {"role": "assistant", "content": "Also short"}
        ]
        result = trim_messages(messages, max_tokens=10000)
        assert len(result) == 2

    def test_trim_over_limit(self):
        """测试超过限制"""
        long_content = "x" * 1000
        messages = [
            {"role": "user", "content": long_content},
            {"role": "assistant", "content": long_content},
            {"role": "user", "content": long_content},
        ]
        result = trim_messages(messages, max_tokens=500)
        assert len(result) < len(messages)

    def test_trim_preserves_order(self):
        """测试裁剪保留最新消息"""
        messages = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Last"},
        ]
        result = trim_messages(messages, max_tokens=1)
        assert result[-1]["content"] == "Last"


class TestAgentMemory:
    """AgentMemory 内存存储测试"""

    def setup_method(self):
        self.memory = AgentMemory()

    def test_add_message_single(self):
        """测试添加单条消息"""
        self.memory.add_message("user1", "user", "Hello")
        history = self.memory.get_history("user1")
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"

    def test_add_message_multiple(self):
        """测试添加多条消息"""
        self.memory.add_message("user1", "user", "Hello")
        self.memory.add_message("user1", "assistant", "Hi there")
        history = self.memory.get_history("user1")
        assert len(history) == 3

    def test_get_history_limit(self):
        """测试历史记录限制"""
        for i in range(60):
            self.memory.add_message("user1", "user", f"Message {i}")
        history = self.memory.get_history("user1", limit=10)
        assert len(history) == 10

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
        self.memory.clear("nonexistent")

    def test_context_count(self):
        """测试获取上下文条数"""
        self.memory.add_message("user1", "user", "Hello")
        self.memory.add_message("user1", "assistant", "Hi")
        count = self.memory.get_context_count("user1")
        assert count == 2

    def test_trim_context(self):
        """测试裁剪上下文"""
        for i in range(20):
            self.memory.add_message("user1", "user", f"Msg {i}")
        removed = self.memory.trim_context("user1", keep_last=5)
        assert removed == 15
        assert len(self.memory.get_history("user1")) == 5

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
        test_user = "test_singleton_user"
        agent_memory.add_message(test_user, "user", "Singleton test")
        history = agent_memory.get_history(test_user)
        assert len(history) >= 1
        agent_memory.clear(test_user)
