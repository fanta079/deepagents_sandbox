"""
API 性能基准测试

使用 Locust 进行负载测试：

    # 单进程测试
    locust -f tests/benchmark.py --host=http://localhost:8000

    # 分布式测试（主进程）
    locust -f tests/benchmark.py --master --host=http://localhost:8000

    # 分布式测试（Worker 进程）
    locust -f tests/benchmark.py --worker --master-host=<master-ip>

    # Web UI 模式
    locust -f tests/benchmark.py --host=http://localhost:8000 --web-port 8089

    # 命令行快速测试（无 Web UI）
    locust -f tests/benchmark.py --host=http://localhost:8000 \
        --headless -u 10 -r 5 -t 60s --run-time 60s
"""
from locust import HttpUser, task, between


class DeepAgentsBenchmark(HttpUser):
    """DeepAgents API 性能基准测试用户"""

    wait_time = between(0.1, 0.5)

    @task
    def health_check(self):
        """健康检查接口"""
        self.client.get("/health")

    @task(3)
    def chat(self):
        """Agent 对话接口（高频）"""
        self.client.post(
            "/api/v1/agent/chat",
            json={
                "messages": [{"role": "user", "content": "Hello"}]
            },
            name="/api/v1/agent/chat"
        )

    @task(2)
    def list_tasks(self):
        """任务列表接口（中频）"""
        self.client.get("/api/v1/tasks/", name="/api/v1/tasks/")

    @task(1)
    def health_detailed(self):
        """详细健康检查"""
        self.client.get("/health/detailed")
