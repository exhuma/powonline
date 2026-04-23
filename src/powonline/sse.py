"""
Server-Sent Events (SSE) in-process event bus.

Provides a lightweight publish/subscribe mechanism scoped by event_id.
Each connected SSE client gets its own asyncio.Queue; published messages
are fan-out broadcast to every queue registered for the given event_id.
"""

import asyncio
import json
import logging
from collections import defaultdict
from typing import AsyncGenerator

LOG = logging.getLogger(__name__)

# event_id -> list of queues, one per connected client
_subscriptions: dict[int, list[asyncio.Queue]] = defaultdict(list)

# Heartbeat interval in seconds — keeps connections alive through proxies
_HEARTBEAT_INTERVAL = 15


async def subscribe(event_id: int) -> asyncio.Queue:
    """Register a new client for *event_id* and return its queue."""
    queue: asyncio.Queue = asyncio.Queue()
    _subscriptions[event_id].append(queue)
    LOG.debug(
        "SSE client subscribed to event %s (%d total)",
        event_id,
        len(_subscriptions[event_id]),
    )
    return queue


def unsubscribe(event_id: int, queue: asyncio.Queue) -> None:
    """Remove *queue* from the subscriber list for *event_id*."""
    try:
        _subscriptions[event_id].remove(queue)
    except ValueError:
        pass
    LOG.debug(
        "SSE client unsubscribed from event %s (%d remaining)",
        event_id,
        len(_subscriptions[event_id]),
    )
    # Clean up the key when no subscribers remain
    if not _subscriptions[event_id]:
        del _subscriptions[event_id]


async def publish(event_id: int, event_type: str, payload: object) -> None:
    """Fan-out *payload* to all clients subscribed to *event_id*."""
    message = json.dumps({"type": event_type, "data": payload})
    queues = list(_subscriptions.get(event_id, []))
    LOG.debug(
        "SSE publish event_id=%s type=%s to %d client(s)",
        event_id,
        event_type,
        len(queues),
    )
    for queue in queues:
        await queue.put(message)


async def event_stream(
    event_id: int, queue: asyncio.Queue
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE-formatted strings.

    Yields a ``data:`` line for each published message and a comment-based
    heartbeat every *_HEARTBEAT_INTERVAL* seconds so that reverse proxies
    (nginx, etc.) do not close idle connections.
    """
    try:
        while True:
            try:
                message = await asyncio.wait_for(
                    queue.get(), timeout=_HEARTBEAT_INTERVAL
                )
                yield f"data: {message}\n\n"
            except asyncio.TimeoutError:
                # Heartbeat — keeps the TCP connection and proxy buffers alive
                yield ": ping\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        unsubscribe(event_id, queue)
