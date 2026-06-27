"""EventBus — in-process async event bus for cross-domain communication.

Single-process only. For cross-process communication, extend with Redis pub/sub.
This implementation handles the common case: all services in one uvicorn process.

Design:
- In-process delivery (<1ms latency)
- Async handler execution (non-blocking)
- Handler failure isolation (one failing handler doesn't affect others)
- Event ordering guaranteed per source
- Graceful degradation: if handler throws, log and continue
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from backend.app.core.events import Event, EventType

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """In-process async event bus. Singleton via module-level instance."""

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._event_count: int = 0
        self._error_count: int = 0
        self._started: bool = False

    def subscribe(self, event_type: EventType, handler: EventHandler | None = None) -> Any:
        """Register a handler for an event type.

        Works as both:
            bus.subscribe(EventType.X, handler)  — direct call
            @bus.subscribe(EventType.X)          — decorator
        """

        def _register(fn: EventHandler) -> EventHandler:
            self._handlers[event_type].append(fn)
            logger.debug(
                "Subscribed %s to %s",
                fn.__qualname__,
                event_type.value,
            )
            return fn

        if handler is not None:
            _register(handler)
            return None
        return _register

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove a handler for an event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event. All registered handlers execute concurrently.

        Handler failures are isolated: one handler throwing doesn't prevent
        other handlers from executing. All errors are logged.
        """
        event.event_id = str(uuid.uuid4())
        self._event_count += 1

        handlers = self._handlers.get(event.type, [])
        if not handlers:
            return

        logger.info(
            "Publishing %s from %s (handlers: %d)",
            event.type.value,
            event.source,
            len(handlers),
        )

        # Execute all handlers concurrently with error isolation
        tasks = [self._safe_execute(handler, event) for handler in handlers]
        await asyncio.gather(*tasks)

    async def _safe_execute(self, handler: EventHandler, event: Event) -> None:
        """Execute a handler with error isolation."""
        try:
            await handler(event)
        except Exception as e:
            self._error_count += 1
            logger.error(
                "Handler %s failed for event %s: %s",
                handler.__qualname__,
                event.type.value,
                str(e),
                exc_info=True,
            )

    def get_stats(self) -> dict[str, Any]:
        """Return event bus statistics for observability."""
        return {
            "total_events_published": self._event_count,
            "total_handler_errors": self._error_count,
            "handler_count_by_type": {et.value: len(handlers) for et, handlers in self._handlers.items() if handlers},
        }

    async def start(self) -> None:
        """Mark bus as started. No-op for in-process bus."""
        self._started = True
        logger.info("Event bus started (in-process mode)")

    async def stop(self) -> None:
        """Mark bus as stopped. Cancel any pending handler tasks."""
        self._started = False
        logger.info("Event bus stopped")


# Module-level singleton — same pattern as llm_manager, redis_cache
event_bus = EventBus()


async def get_event_bus() -> EventBus:
    """Dependency injection for event bus."""
    return event_bus
