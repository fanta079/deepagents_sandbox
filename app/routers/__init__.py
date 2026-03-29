"""
Routers — FastAPI 路由聚合
"""

from app.routers import agent, example, sse, users, tasks, files, websocket, auth, rag

__all__ = ["agent", "example", "sse", "users", "tasks", "files", "websocket", "auth", "rag"]
