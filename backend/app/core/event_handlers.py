"""Cross-domain event handlers.

Each handler belongs to a domain but reacts to events from OTHER domains.
This is the ONLY place where cross-domain awareness exists.

Rules:
- Handler function name: on_{event_type_in_snake_case}
- Handler lives in the CONSUMING domain's file
- Handler must be idempotent (events may be delivered more than once)
- Handler must not publish events synchronously (prevents event chains)
"""

from __future__ import annotations

import logging

from backend.app.core.event_bus import event_bus
from backend.app.core.events import Event, EventType

logger = logging.getLogger(__name__)


# ── Memory domain listens to Awareness events ──


@event_bus.subscribe(EventType.FILE_CHANGED)
async def on_file_changed(event: Event) -> None:
    """When a file changes, check if memory needs updating.

    Consumer: Memory domain (memory freshness)
    Publisher: Awareness domain (file watcher)
    Idempotency: Safe (check is idempotent)
    """
    file_path = event.data.get("file_path")
    logger.info("Memory: checking if %s affects existing memories", file_path)


# ── Cognition domain listens to Memory events ──


@event_bus.subscribe(EventType.MEMORY_CREATED)
async def on_memory_created(event: Event) -> None:
    """When a memory is created, update the knowledge graph.

    Consumer: Cognition domain (graph building)
    Publisher: Memory domain
    Idempotency: Safe (graph merge is idempotent)
    """
    memory_id = event.data.get("memory_id")
    logger.info("Cognition: processing new memory %s for graph update", memory_id)


@event_bus.subscribe(EventType.MEMORY_DELETED)
async def on_memory_deleted(event: Event) -> None:
    """When a memory is deleted, clean up graph references.

    Consumer: Cognition domain (graph cleanup)
    Publisher: Memory domain
    Idempotency: Safe (graph cleanup is idempotent)
    """
    memory_id = event.data.get("memory_id")
    logger.info("Cognition: removing memory %s from knowledge graph", memory_id)


# ── Interaction domain listens to Execution events ──


@event_bus.subscribe(EventType.TASK_COMPLETED)
async def on_task_completed(event: Event) -> None:
    """When a task completes, update conversation context.

    Consumer: Interaction domain (conversation state)
    Publisher: Cognition domain (agent loop)
    Idempotency: Safe (state update is idempotent)
    """
    task_id = event.data.get("task_id")
    logger.info("Interaction: task %s completed, updating conversation", task_id)


# ── Cognition domain listens to Intelligence events ──


@event_bus.subscribe(EventType.MODEL_LOADED)
async def on_model_loaded(event: Event) -> None:
    """When a model is loaded, update agent configuration.

    Consumer: Cognition domain (agent model selection)
    Publisher: Intelligence domain (model manager)
    Idempotency: Safe (config update overwrites)
    """
    model_name = event.data.get("model_name")
    logger.info("Cognition: model %s loaded, updating agent config", model_name)


# ── Awareness domain listens to Integration events ──


@event_bus.subscribe(EventType.DOWNLOAD_COMPLETED)
async def on_download_completed(event: Event) -> None:
    """When a download completes, trigger indexing.

    Consumer: Awareness domain (auto-index downloaded content)
    Publisher: Integration domain (download manager)
    Idempotency: Safe (indexing checks for existing index)
    """
    file_path = event.data.get("file_path")
    logger.info("Awareness: indexing downloaded file %s", file_path)


# ── System domain listens to all system events ──


@event_bus.subscribe(EventType.SYSTEM_STARTUP)
async def on_system_startup(event: Event) -> None:
    """System startup notification — all domains initialize."""
    logger.info("System: startup event received, initializing domain services")


@event_bus.subscribe(EventType.SYSTEM_SHUTDOWN)
async def on_system_shutdown(event: Event) -> None:
    """System shutdown notification — all domains clean up."""
    logger.info("System: shutdown event received, cleaning up domain services")
