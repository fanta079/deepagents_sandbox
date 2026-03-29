"""
Locust 负载测试主文件

快速启动：
    locust --host=http://localhost:8000

或指定端口：
    locust --host=http://localhost:8000 --web-port 8089

headless 模式（无 Web UI）：
    locust --host=http://localhost:8000 --headless -u 50 -r 10 -t 60s
"""
from locust import HttpUser, task, between


class APIUser(HttpUser):
    """API 通用负载测试用户"""

    wait_time = between(1, 3)

    @task
    def health(self):
        """基础健康检查"""
        self.client.get("/health")

    @task
    def detailed_health(self):
        """详细健康检查"""
        self.client.get("/health/detailed")

    @task
    def root(self):
        """根路径"""
        self.client.get("/")

    @task
    def docs(self):
        """API 文档"""
        self.client.get("/docs")
