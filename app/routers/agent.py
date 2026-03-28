"""
DeepAgent 路由 - 通过 FastAPI 暴露 Agent 接口
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncIterator

from app.core.rate_limit import limiter

from app.sandbox.agent_runner import SandboxAgent, get_agent, shutdown_agent

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    backend: str = "opensandbox"  # opensandbox, daytona, modal
    stream: bool = False


class ChatResponse(BaseModel):
    message: str
    finish_reason: Optional[str] = None
    backend: str


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(request: Request, request_body: ChatRequest):
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
async def chat_stream(request: Request, request_body: ChatRequest):
    """与 Agent 对话（流式版本，通过 SSE）"""
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
async def reset_agent(backend: str = "opensandbox"):
    """重置 Agent（销毁旧沙箱，重新冷启动）"""
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
async def health():
    """健康检查"""
    return {"status": "ok", "backend": "opensandbox"}
