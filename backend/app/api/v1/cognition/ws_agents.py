"""WebSocket endpoint for real-time agent run progress."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select

from backend.app.core.db import verify_ws_token
from backend.app.core.websocket import manager
from backend.app.db.session import SessionLocal
from backend.app.models.cognition.agent import AgentRun, AgentStep

router = APIRouter()


def _extract_ws_token(ws: WebSocket, token: str | None = None) -> str | None:
    """Extract JWT from query param, sec-websocket-protocol header, or cookie."""
    if token:
        return token
    protocols = ws.headers.get("sec-websocket-protocol", "")
    if protocols:
        return protocols.split(",")[0].strip() if "," in protocols else protocols.strip()
    return ws.cookies.get("cortex_access")


def _fetch_agent_runs(user_id: str) -> dict:
    """Fetch active agent runs with step progress."""
    db = SessionLocal()
    try:
        stmt = (
            select(AgentRun)
            .where(AgentRun.user_id == int(user_id))
            .where(AgentRun.status.in_(["running", "pending"]))
            .order_by(AgentRun.created_at.desc())
            .limit(10)
        )
        result = db.execute(stmt)
        runs = result.scalars().all()

        run_data = []
        for run in runs:
            completed_stmt = (
                select(func.count(AgentStep.id))
                .where(AgentStep.run_id == run.id)
                .where(AgentStep.status == "completed")
            )
            completed = db.execute(completed_stmt).scalar() or 0

            total_stmt = select(func.count(AgentStep.id)).where(AgentStep.run_id == run.id)
            total = db.execute(total_stmt).scalar() or 0

            run_data.append(
                {
                    "id": run.id,
                    "agent_id": run.agent_id,
                    "status": run.status,
                    "completed_steps": completed,
                    "total_steps": total,
                    "progress": completed / total if total > 0 else 0,
                    "created_at": str(run.created_at),
                }
            )

        return {"type": "agent_runs", "runs": run_data}
    finally:
        db.close()


@router.websocket("/ws/agents")
async def agents_ws(ws: WebSocket, token: str = Query(None)):
    """Push agent run status updates every 2 seconds."""
    token = _extract_ws_token(ws, token)
    if not token:
        await ws.close(code=4001, reason="Authentication required")
        return
    try:
        user_id = await verify_ws_token(token)
    except Exception:
        await ws.close(code=4001, reason="Invalid token or account deleted")
        return

    await manager.connect(ws, channel=f"agents:{user_id}", user_id=int(user_id))
    try:
        while True:
            try:
                data = _fetch_agent_runs(user_id)
            except Exception:
                data = {"type": "agent_runs", "runs": []}
            await manager.send(ws, data)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(ws, channel=f"agents:{user_id}", user_id=int(user_id))
