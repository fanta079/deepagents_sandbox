from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
import time

router = APIRouter()


@router.get("/sse")
def sse_endpoint():
    async def event_stream():
        async def generate():
            for i in range(10):
                data = json.dumps({
                    "index": i,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "message": f"Event #{i + 1}"
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
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sse/clock")
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
