"""In-memory stream manager for decoupled chat generation.

Background tasks push chunks into per-conversation buffers.
Frontend SSE consumers read from those buffers. Disconnection
does not cancel generation — the buffer retains undelivered chunks
and the response is always written to DB.

Supports resubscribe via catch-up: when a new consumer connects,
it receives ALL historical events before continuing with live events.
This handles tab-switch / reconnection scenarios where the old consumer
consumed chunks from the queue that a new consumer needs.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Maximum chunks retained in buffer before oldest are dropped
_MAX_BUFFER_SIZE = 4096
# How long (seconds) a completed buffer stays available for reconnection
_BUFFER_TTL = 600  # 10 minutes


@dataclass
class StreamBuffer:
    """Buffer for a single conversation's streaming response.

    Supports multiple consumers via catch-up: all pushed events are
    stored in ``_history``. When a new consumer connects, it receives
    the full history first, then continues reading live events from
    the queue. This handles tab-switch / reconnection scenarios.
    """

    conversation_id: int
    queue: asyncio.Queue[str] = field(default_factory=lambda: asyncio.Queue(maxsize=_MAX_BUFFER_SIZE))
    done: bool = False
    final_data: dict | None = None  # The 'done' event payload
    error: str | None = None
    created_at: float = field(default_factory=time.time)

    # Catch-up: every SSE event string ever pushed (sentinel excluded)
    _history: list[str] = field(default_factory=list)

    def push(self, data: str) -> None:
        """Push an SSE event string into the buffer (non-blocking drop if full)."""
        self._history.append(data)
        try:
            self.queue.put_nowait(data)
        except asyncio.QueueFull:
            # Drop oldest to make room — better than blocking the generator
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                self.queue.put_nowait(data)
            except asyncio.QueueFull:
                pass

    def mark_done(self, final_data: dict | None = None, error: str | None = None) -> None:
        """Mark generation as complete. Pushes a sentinel for consumers."""
        self.done = True
        self.final_data = final_data
        self.error = error
        # Push sentinel so waiting consumers wake up
        self.queue.put_nowait(None)  # type: ignore[arg-type]

    def get_catch_up(self) -> list[str]:
        """Get all historical events and drain the queue.

        Returns a snapshot of every event ever pushed. Also clears the
        queue so that subsequent ``read()`` calls return only NEW events
        (pushed after this call).
        """
        events = list(self._history)
        # Drain the queue — catch-up covers everything already in it
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        return events

    async def read(self, timeout: float = 30.0) -> str | None:
        """Read next chunk from buffer. Returns None when done and buffer empty."""
        try:
            chunk = await asyncio.wait_for(self.queue.get(), timeout=timeout)
            return chunk
        except asyncio.TimeoutError:
            if self.done:
                return None
            return ""  # Keep-alive

    def is_stale(self) -> bool:
        """Check if this buffer is old enough to garbage collect."""
        return time.time() - self.created_at > _BUFFER_TTL


class StreamManager:
    """Singleton managing per-conversation stream buffers, background tasks,
    and tool approval queues."""

    def __init__(self) -> None:
        self._buffers: dict[int, StreamBuffer] = {}
        self._tasks: dict[int, asyncio.Task] = {}
        # Approval queues: conversation_id → {call_id: asyncio.Future[bool]}
        self._approval_queues: dict[int, dict[str, asyncio.Future[bool]]] = {}

    def get_or_create_buffer(self, conversation_id: int) -> StreamBuffer:
        """Get existing buffer or create a new one."""
        if conversation_id not in self._buffers or self._buffers[conversation_id].done:
            self._buffers[conversation_id] = StreamBuffer(conversation_id=conversation_id)
        return self._buffers[conversation_id]

    def get_buffer(self, conversation_id: int) -> StreamBuffer | None:
        """Get buffer if it exists and isn't done (or has undelivered chunks)."""
        buf = self._buffers.get(conversation_id)
        if buf is None:
            return None
        if buf.is_stale():
            self._cleanup(conversation_id)
            return None
        return buf

    async def wait_for_buffer(self, conversation_id: int, timeout: float = 10.0) -> StreamBuffer | None:
        """Wait for a buffer to be created for this conversation.

        Used when the SSE subscriber might connect before the POST handler
        has finished creating the buffer. Polls every 50ms until found.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            buf = self._buffers.get(conversation_id)
            if buf is not None:
                return buf
            await asyncio.sleep(0.05)
        return None

    def register_task(self, conversation_id: int, task: asyncio.Task) -> None:
        """Register a background generation task."""
        # Cancel previous task for this conversation if any
        prev = self._tasks.get(conversation_id)
        if prev and not prev.done():
            prev.cancel()
        self._tasks[conversation_id] = task

    def cancel_generation(self, conversation_id: int) -> bool:
        """Cancel an in-progress generation. Returns True if cancelled."""
        task = self._tasks.get(conversation_id)
        if task and not task.done():
            task.cancel()
            buf = self._buffers.get(conversation_id)
            if buf and not buf.done:
                buf.mark_done(error="Generation cancelled")
            return True
        return False

    def _cleanup(self, conversation_id: int) -> None:
        """Remove stale buffer and task."""
        self._buffers.pop(conversation_id, None)
        self._tasks.pop(conversation_id, None)
        # Cancel any pending approval futures
        approvals = self._approval_queues.pop(conversation_id, {})
        for future in approvals.values():
            if not future.done():
                future.set_result(False)

    def create_approval_future(self, conversation_id: int, call_id: str) -> asyncio.Future[bool]:
        """Create a future that the generation task awaits for user approval."""
        if conversation_id not in self._approval_queues:
            self._approval_queues[conversation_id] = {}
        loop = asyncio.get_event_loop()
        future: asyncio.Future[bool] = loop.create_future()
        self._approval_queues[conversation_id][call_id] = future
        return future

    def resolve_approval(self, conversation_id: int, call_id: str, approved: bool) -> bool:
        """Resolve a pending approval. Returns True if resolved, False if not found."""
        queues = self._approval_queues.get(conversation_id, {})
        future = queues.pop(call_id, None)
        if future and not future.done():
            future.set_result(approved)
            return True
        return False

    def gc(self) -> int:
        """Garbage collect stale buffers. Returns count removed."""
        stale = [cid for cid, buf in self._buffers.items() if buf.is_stale()]
        for cid in stale:
            self._cleanup(cid)
        return len(stale)


# Global singleton
stream_manager = StreamManager()
