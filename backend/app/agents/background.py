"""Background agent execution with status tracking."""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

_active_runs: dict[int, asyncio.Task] = {}


async def run_agent_background(run_id: int, agent_id: int, user_id: int, input_text: str):
    from backend.app.agents.run_manager import AgentRunManager
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        manager = AgentRunManager(db)
        _active_runs[run_id] = asyncio.current_task()
        await manager.run_agent(agent_id=agent_id, user_id=user_id, input_text=input_text)
    except Exception as e:
        logger.error("Background agent run %d failed: %s", run_id, e)
    finally:
        _active_runs.pop(run_id, None)
        db.close()


def get_run_status(run_id: int) -> str:
    if run_id in _active_runs:
        task = _active_runs[run_id]
        return "completed" if task.done() else "running"
    return "unknown"
