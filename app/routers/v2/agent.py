"""
Agent 路由 v2 — 支持多 Agent 并行对话

路径前缀: /api/v2/agent（由 main.py 控制版本前缀）
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncIterator, Dict

from app.core.rate_limit import limiter

from app.sandbox.agent_runner import SandboxAgent, get_agent, shutdown_agent

router = APIRouter(prefix="/agent", tags=["agent"])


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    backend: str = "opensandbox"
    stream: bool = False


class ChatResponse(BaseModel):
    message: str
    finish_reason: Optional[str] = None
    backend: str


class BatchChatRequest(BaseModel):
    """v2 批量对话请求"""
    sessions: List[Dict[str, List[Message]]]  # [{"id": "session1", "messages": [...]}]


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_v2(request: Request, request_body: ChatRequest):
    """与 Agent 对话"""
    try:
        agent_instance = await get_agent(backend_type=request_body.backend)
        result = await agent_instance.invoke([m.model_dump() for m in request_body.messages])
        return ChatResponse(
            message=result["messages"][-1].content,
            finish_reason="stop",
            backend=request_body.backend,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream_v2(request: Request, request_body: ChatRequest):
    """与 Agent 对话（流式版本）"""
    async def event_generator() -> AsyncIterator[str]:
        try:
            agent_instance = await get_agent(backend_type=request_body.backend)
            result = agent_instance.agent.invoke(
                {"messages": [m.model_dump() for m in request_body.messages]},
                stream=True,
            )
            for chunk in result:
                if chunk.get("messages"):
                    content = chunk["messages"][-1].content
                    if content:
                        yield f"data: {content}\n\n"
                elif chunk.get("type") == "content_block_delta":
                    yield f"data: {chunk['content']}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/reset")
async def reset_agent_v2(backend: str = "opensandbox"):
    """重置 Agent"""
    try:
        await shutdown_agent()
        return {
            "status": "reset",
            "message": f"{backend} 沙箱已重置，下次请求会自动冷启动",
            "backend": backend,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_v2():
    """健康检查"""
    return {"status": "ok", "backend": "opensandbox", "version": "v2"}


@router.post("/backends", response_model=dict)
async def list_backends():
    """列出所有可用 Agent 后端"""
    return {
        "backends": [
            {"name": "opensandbox", "status": "available"},
            {"name": "daytona", "status": "available"},
            {"name": "modal", "status": "available"},
        ]
    }
