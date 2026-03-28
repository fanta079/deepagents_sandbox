"""
WebSocket 路由 — 实时聊天/通知示例
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 在线连接集合
        self.active_connections: Set[WebSocket] = set()
        # 用户 -> WebSocket 映射
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str = "anonymous"):
        """接受并注册连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.user_connections[user_id] = websocket
        # 广播用户上线通知
        await self.broadcast_system(f"用户 {user_id} 已连接，当前在线 {len(self.active_connections)} 人")

    def disconnect(self, websocket: WebSocket, user_id: str = "anonymous"):
        """移除连接"""
        self.active_connections.discard(websocket)
        self.user_connections.pop(user_id, None)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """向单个连接发送消息"""
        await websocket.send_text(message)

    async def broadcast(self, message: str, sender: WebSocket):
        """广播消息给所有连接（除发送者外）"""
        disconnected = set()
        for connection in self.active_connections:
            if connection != sender:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.add(connection)
        # 清理失效连接
        for conn in disconnected:
            self.active_connections.discard(conn)

    async def broadcast_system(self, message: str):
        """系统消息广播给所有连接"""
        msg_data = {
            "type": "system",
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        json_msg = json.dumps(msg_data)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json_msg)
            except Exception:
                self.active_connections.discard(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: str = "anonymous"):
    """
    WebSocket 端点: WS /ws?user_id=xxx

    支持:
    - 广播消息给所有在线用户
    - 个人消息（发送 {"to": "user_id", "content": "..."}）
    - 系统消息 {"type": "system", "content": "..."}
    """
    await manager.connect(websocket, user_id)
    try:
        await websocket.send_text(json.dumps({
            "type": "system",
            "content": f"欢迎 {user_id}，已连接到 WebSocket 服务器",
            "timestamp": datetime.utcnow().isoformat(),
        }))

        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                # 非 JSON 当作普通广播消息
                msg_data = {
                    "type": "message",
                    "user_id": user_id,
                    "content": data,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await manager.broadcast(json.dumps(msg_data), sender=websocket)
                continue

            msg_type = payload.get("type", "message")

            if msg_type == "system":
                await manager.broadcast_system(payload.get("content", ""))
            elif msg_type == "personal":
                # {"to": "user_id", "content": "..."}
                target_user = payload.get("to")
                msg_data = {
                    "type": "personal",
                    "from": user_id,
                    "content": payload.get("content", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                target_ws = manager.user_connections.get(target_user)
                if target_ws:
                    await target_ws.send_text(json.dumps(msg_data))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "system",
                        "content": f"用户 {target_user} 不在线",
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
            else:
                # 普通广播
                msg_data = {
                    "type": "message",
                    "user_id": user_id,
                    "content": payload.get("content", data),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await manager.broadcast(json.dumps(msg_data), sender=websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        await manager.broadcast_system(
            f"用户 {user_id} 已断开连接，当前在线 {len(manager.active_connections)} 人"
        )
    except Exception:
        manager.disconnect(websocket, user_id)
