"""
SSE endpoint — publicly readable real-time stream per event.

GET /events/{event_id}/stream

Clients receive newline-delimited JSON messages of the form:
    data: {"type": "<event-type>", "data": {...}}\n\n

A comment heartbeat (": ping") is emitted every 15 s to keep the
connection alive through reverse proxies (nginx X-Accel-Buffering: no).
"""

import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from powonline import sse

ROUTER = APIRouter(prefix="/events/{event_id}", tags=["sse"])
LOG = logging.getLogger(__name__)


@ROUTER.get("/stream")
async def event_stream(event_id: int) -> StreamingResponse:
    """
    Open a Server-Sent Events stream for *event_id*.

    No authentication is required — streams are intentionally public so
    that dashboard displays (e.g. on a TV) work without a login session.
    """
    queue = await sse.subscribe(event_id)
    return StreamingResponse(
        sse.event_stream(event_id, queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx proxy buffering
            "Connection": "keep-alive",
        },
    )
