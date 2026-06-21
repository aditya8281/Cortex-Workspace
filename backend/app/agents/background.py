"""Background agent execution with status tracking and SSE event queues."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

_active_runs: dict[int, asyncio.Task] = {}
_event_queues: dict[int, list[asyncio.Queue]] = {}


def subscribe(run_id: int) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    _event_queues.setdefault(run_id, []).append(queue)
    return queue


def unsubscribe(run_id: int, queue: asyncio.Queue) -> None:
    queues = _event_queues.get(run_id, [])
    if queue in queues:
        queues.remove(queue)


async def _emit(run_id: int, event: dict[str, Any]) -> None:
    for queue in _event_queues.get(run_id, []):
        await queue.put(event)


async def run_agent_background(run_id: int, agent_id: int, user_id: int, input_text: str):
    from backend.app.agents.run_manager import AgentRunManager
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        manager = AgentRunManager(db, event_callback=lambda e: asyncio.create_task(_emit(run_id, e)))
        _active_runs[run_id] = asyncio.current_task()
        await manager.run_agent(agent_id=agent_id, user_id=user_id, input_text=input_text)
    except Exception as e:
        logger.error("Background agent run %d failed: %s", run_id, e)
        await _emit(run_id, {"type": "error", "message": str(e)})
    finally:
        _active_runs.pop(run_id, None)
        await _emit(run_id, {"type": "_done"})
        db.close()


def get_run_status(run_id: int) -> str:
    if run_id in _active_runs:
        task = _active_runs[run_id]
        return "completed" if task.done() else "running"
    return "unknown"
