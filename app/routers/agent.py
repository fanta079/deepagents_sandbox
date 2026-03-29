"""
DeepAgent 路由 - 通过 FastAPI 暴露 Agent 接口
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncIterator

from app.core.rate_limit import limiter, get_user_id
from app.core.memory import agent_memory
from app.core.config import settings
from app.sandbox.agent_runner import SandboxAgent, get_agent, shutdown_agent

router = APIRouter(prefix="/agent", tags=["agent"])


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    backend: str = "opensandbox"  # opensandbox, daytona, modal
    stream: bool = False
    clear_context: bool = False  # 用户主动清空上下文


class ChatResponse(BaseModel):
    message: str
    finish_reason: Optional[str] = None
    backend: str


def _auto_trim(user_id: str) -> None:
    """自动裁剪上下文，防止超过限制"""
    count = agent_memory.get_context_count(user_id)
    if count > settings.MAX_CONTEXT_MESSAGES:
        agent_memory.trim_context(user_id, settings.MAX_CONTEXT_MESSAGES)


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(request: Request, request_body: ChatRequest):
    """与 Agent 对话"""
    try:
        user_id = get_user_id(request)

        # 用户主动清空上下文
        if request_body.clear_context:
            agent_memory.clear(user_id)

        # 保存用户消息到记忆
        for msg in request_body.messages:
            agent_memory.add_message(user_id, msg.role, msg.content)

        # 自动裁剪超长上下文
        _auto_trim(user_id)

        agent_instance = await get_agent(backend_type=request_body.backend)
        result = await agent_instance.invoke([m.model_dump() for m in request_body.messages])

        # 保存 Agent 响应到记忆
        response_content = result["messages"][-1].content
        agent_memory.add_message(user_id, "assistant", response_content)

        return ChatResponse(
            message=response_content,
            finish_reason="stop",
            backend=request_body.backend,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request, request_body: ChatRequest):
    """与 Agent 对话（流式版本，通过 SSE）"""
    user_id = get_user_id(request)

    # 用户主动清空上下文
    if request_body.clear_context:
        agent_memory.clear(user_id)

    async def event_generator() -> AsyncIterator[str]:
        try:
            # 保存用户消息到记忆
            for msg in request_body.messages:
                agent_memory.add_message(user_id, msg.role, msg.content)

            # 自动裁剪超长上下文
            _auto_trim(user_id)

            agent_instance = await get_agent(backend_type=request_body.backend)
            result = agent_instance.agent.invoke(
                {"messages": [m.model_dump() for m in request_body.messages]},
                stream=True,
            )
            response_parts = []
            for chunk in result:
                if chunk.get("messages"):
                    content = chunk["messages"][-1].content
                    if content:
                        response_parts.append(content)
                        yield f"data: {content}\n\n"
                elif chunk.get("type") == "content_block_delta":
                    part = chunk['content']
                    response_parts.append(part)
                    yield f"data: {part}\n\n"
            # 保存 Agent 响应到记忆
            full_response = "".join(response_parts)
            if full_response:
                agent_memory.add_message(user_id, "assistant", full_response)
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


# ——— 上下文管理端点 ——————————————————————————————————————————

@router.post("/context/clear")
async def clear_context(request: Request):
    """用户主动清空上下文"""
    user_id = get_user_id(request)
    agent_memory.clear(user_id)
    return {"message": "上下文已清空", "user_id": user_id}


@router.get("/context/info")
async def context_info(request: Request):
    """获取上下文状态"""
    user_id = get_user_id(request)
    count = agent_memory.get_context_count(user_id)
    history = agent_memory.get_history(user_id, limit=5)
    return {
        "user_id": user_id,
        "message_count": count,
        "recent_messages": history
    }


@router.post("/context/trim")
async def trim_context(request: Request, keep_last: int = 10):
    """裁剪上下文，防止过长"""
    user_id = get_user_id(request)
    removed = agent_memory.trim_context(user_id, keep_last)
    return {"message": f"已裁剪 {removed} 条消息", "remaining": keep_last}


# ——— 其他端点 ————————————————————————————————————————————————

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
