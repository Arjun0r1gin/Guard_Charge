import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/stream", tags=["stream"])

# In-memory async queue shared across SSE subscribers.
# Each subscriber gets its own queue fed by the broadcast helper.
_subscribers: list[asyncio.Queue] = []


class LogLine(BaseModel):
    text: str


def _broadcast(text: str):
    """Push a log line to every connected SSE client (non-async, safe to call from sync context)."""
    dead = []
    for q in _subscribers:
        try:
            q.put_nowait(text)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _subscribers.remove(q)


@router.post("/log")
async def post_log(line: LogLine):
    """Simulator calls this for every print() line.
    Split on newlines so embedded \\n chars don't break SSE format.
    Each segment becomes its own SSE event.
    """
    for segment in line.text.split("\n"):
        _broadcast(segment)
    return {"ok": True}


@router.get("/events")
async def sse_stream():
    """Browser connects here to receive simulator output as SSE."""
    q: asyncio.Queue = asyncio.Queue(maxsize=500)
    _subscribers.append(q)

    async def event_generator():
        try:
            while True:
                text = await q.get()
                # SSE format: data: <payload>\n\n
                yield f"data: {text}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if q in _subscribers:
                _subscribers.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
