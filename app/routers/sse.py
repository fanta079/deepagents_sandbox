from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
import time

router = APIRouter(prefix="/sse", tags=["SSE"])


@router.get("")
def sse_endpoint():
    async def event_stream():
        for i in range(10):
            data = json.dumps({
                "index": i,
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"Event #{i + 1}"
            })
            yield f"data: {data}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/clock")
def sse_clock():
    """实时时钟 SSE 流"""
    async def generate():
        while True:
            data = json.dumps({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": time.time()
            })
            yield f"data: {data}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ——— 流式思考输出端点 ————————————————————————————————————————————————


@router.get("/think")
async def sse_think_stream(task_id: str):
    """
    流式思考输出端点

    思考内容将实时流式推送，格式：
    event: think\ndata: {"content": "正在分析..."}\n\n
    event: think\ndata: {"content": "计划步骤..."}\n\n
    event: done\ndata: {"content": "最终结果"}\n\n
    """
    async def think_generator():
        thinking_steps = [
            "理解用户输入...",
            "检索相关知识...",
            "制定执行计划...",
            "执行代码...",
            "验证结果...",
        ]

        for step in thinking_steps:
            yield f"event: think\ndata: {json.dumps({'content': step})}\n\n"
            await asyncio.sleep(0.5)

        yield f"event: done\ndata: {json.dumps({'content': '思考完成', 'task_id': task_id})}\n\n"

    return StreamingResponse(
        think_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
