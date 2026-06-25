"""Agent API — CRUD, runs, steps, and feedback."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.agents.run_manager import AgentRunManager
from backend.app.core.db import get_current_user, get_db
from backend.app.models.agent import AgentFeedback, AgentRun, AgentStep
from backend.app.models.user import User
from backend.app.schemas.agent import (
    AgentCreateResponse,
    AgentFeedbackCreateResponse,
    AgentFeedbackListResponse,
    AgentGetResponse,
    AgentListResponse,
    AgentRunCreateResponse,
    AgentRunGetResponse,
    AgentRunListResponse,
    AgentRunStatusResponse,
    AgentRunStepsResponse,
    AgentUpdateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Payloads ────────────────────────────────────────────────────


class AgentCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    system_prompt: str = Field(min_length=1)
    model_id: str = Field(default="local", max_length=100)
    tools: list[str] | None = None


class AgentUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    system_prompt: str | None = Field(default=None, min_length=1)
    model_id: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    tools: list[str] | None = None


class RunCreatePayload(BaseModel):
    agent_id: int
    input: str = Field(min_length=1)


class FeedbackPayload(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


# ── Runs ────────────────────────────────────────────────────────


@router.post("/agents/runs", response_model=AgentRunCreateResponse)
async def create_run(
    payload: RunCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start an agent run in the background and return immediately."""
    import asyncio

    from backend.app.agents.background import run_agent_background

    manager = AgentRunManager(db)
    agent = manager.get_agent(payload.agent_id, user_id=current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    try:
        run = manager.create_run(payload.agent_id, current_user.id, payload.input)

        async def _run_with_logging():
            try:
                await run_agent_background(run.id, payload.agent_id, current_user.id, payload.input)
            except Exception:
                logger.error("Background agent run %d failed", run.id, exc_info=True)

        task = asyncio.create_task(_run_with_logging())
        task.add_done_callback(
            lambda t: None if not t.exception() else logger.error("Unhandled error in agent task: %s", t.exception())
        )
        return {"status": "started", "run_id": run.id}
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent not found")
    except Exception:
        logger.error("Agent run failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Agent run failed")


@router.get("/agents/runs", response_model=AgentRunListResponse)
def list_runs(
    agent_id: int | None = None,
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List runs for the current user."""
    manager = AgentRunManager(db)
    runs = manager.list_runs(
        agent_id=agent_id,
        user_id=current_user.id,
        status=status,
        limit=limit,
    )
    return {"runs": [manager.serialize_run(r) for r in runs]}


@router.get("/agents/runs/{run_id}", response_model=AgentRunGetResponse)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific run with its steps."""
    manager = AgentRunManager(db)
    run = manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Run not found")

    steps = manager.get_run_steps(run_id)
    return {
        "run": manager.serialize_run(run),
        "steps": [manager.serialize_step(s) for s in steps],
    }


@router.get("/agents/runs/{run_id}/status", response_model=AgentRunStatusResponse)
async def get_run_status_endpoint(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the status of a background agent run."""
    from backend.app.agents.background import get_run_status

    manager = AgentRunManager(db)
    run = manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Run not found")

    return {"run_id": run_id, "status": get_run_status(run_id)}


@router.post("/agents/runs/{run_id}/stream")
async def stream_run_events(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream SSE events for an agent run."""
    import asyncio

    from backend.app.agents.background import subscribe, unsubscribe

    manager = AgentRunManager(db)
    run = manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Run not found")

    queue = subscribe(run_id)

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue

                if event.get("type") == "_done":
                    break

                yield f"data: {json.dumps(event)}\n\n"
        finally:
            unsubscribe(run_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/agents/runs/{run_id}/steps", response_model=AgentRunStepsResponse)
def get_run_steps(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all steps for a run."""
    manager = AgentRunManager(db)
    run = manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Run not found")

    steps = manager.get_run_steps(run_id)
    return {"steps": [manager.serialize_step(s) for s in steps]}


# ── Feedback ────────────────────────────────────────────────────


@router.post("/agents/runs/{run_id}/feedback", response_model=AgentFeedbackCreateResponse)
def add_feedback(
    run_id: int,
    payload: FeedbackPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add feedback for a run."""
    manager = AgentRunManager(db)
    run = manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Run not found")

    try:
        feedback = manager.add_feedback(
            run_id=run_id,
            user_id=current_user.id,
            rating=payload.rating,
            comment=payload.comment,
        )
        return {
            "status": "created",
            "feedback": {
                "id": feedback.id,
                "rating": feedback.rating,
                "comment": feedback.comment,
            },
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input")


@router.get("/agents/runs/{run_id}/feedback", response_model=AgentFeedbackListResponse)
def get_feedback(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all feedback for a run."""
    manager = AgentRunManager(db)
    run = manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Run not found")

    feedback_list = manager.get_run_feedback(run_id)
    return {
        "feedback": [
            {
                "id": f.id,
                "rating": f.rating,
                "comment": f.comment,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in feedback_list
        ]
    }


# ── Metrics ─────────────────────────────────────────────────────


class AgentMetricsResponse(BaseModel):
    total_runs: int
    success_rate: float
    avg_duration_seconds: float | None
    total_steps: int
    avg_steps_per_run: float
    feedback_summary: dict[str, float | int]


@router.get("/agents/metrics", response_model=AgentMetricsResponse)
async def get_agent_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    runs = db.query(AgentRun).filter(AgentRun.user_id == current_user.id).all()
    total_runs = len(runs)

    if total_runs == 0:
        return {
            "total_runs": 0,
            "success_rate": 0.0,
            "avg_duration_seconds": None,
            "total_steps": 0,
            "avg_steps_per_run": 0.0,
            "feedback_summary": {"count": 0, "avg_rating": 0.0},
        }

    completed_runs = [r for r in runs if r.status == "completed"]
    success_rate = len(completed_runs) / total_runs

    durations = []
    for r in runs:
        if r.completed_at and r.created_at:
            duration = (r.completed_at - r.created_at).total_seconds()
            durations.append(duration)
    avg_duration = sum(durations) / len(durations) if durations else None

    total_steps = db.query(AgentStep).join(AgentRun).filter(AgentRun.user_id == current_user.id).count()
    avg_steps = total_steps / total_runs if total_runs > 0 else 0.0

    feedback_stats = (
        db.query(
            func.count(AgentFeedback.id),
            func.coalesce(func.avg(AgentFeedback.rating), 0.0),
        )
        .join(AgentRun)
        .filter(AgentRun.user_id == current_user.id)
        .one()
    )

    return {
        "total_runs": total_runs,
        "success_rate": round(success_rate, 3),
        "avg_duration_seconds": round(avg_duration, 1) if avg_duration is not None else None,
        "total_steps": total_steps,
        "avg_steps_per_run": round(avg_steps, 1),
        "feedback_summary": {
            "count": feedback_stats[0],
            "avg_rating": round(float(feedback_stats[1]), 2),
        },
    }


# ── Agent CRUD ──────────────────────────────────────────────────


@router.get("/agents", response_model=AgentListResponse)
def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agents for the current user."""
    manager = AgentRunManager(db)
    agents = manager.list_agents(user_id=current_user.id)
    return {
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "system_prompt": a.system_prompt,
                "model_id": a.model_id,
                "tools": a.tools_json,
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
            for a in agents
        ]
    }


@router.post("/agents", response_model=AgentCreateResponse)
def create_agent(
    payload: AgentCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new agent."""
    manager = AgentRunManager(db)
    try:
        agent = manager.create_agent(
            name=payload.name,
            description=payload.description,
            system_prompt=payload.system_prompt,
            model_id=payload.model_id,
            user_id=current_user.id,
            tools=payload.tools,
        )
        return {
            "status": "created",
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "system_prompt": agent.system_prompt,
                "model_id": agent.model_id,
                "tools": agent.tools_json,
                "is_active": agent.is_active,
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            },
        }
    except Exception as e:
        logger.error("Failed to create agent: %s", e)
        raise HTTPException(status_code=400, detail="Failed to create agent")


@router.get("/agents/{agent_id}", response_model=AgentGetResponse)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific agent."""
    manager = AgentRunManager(db)
    agent = manager.get_agent(agent_id, user_id=current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "agent": {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "system_prompt": agent.system_prompt,
            "model_id": agent.model_id,
            "tools": agent.tools_json,
            "is_active": agent.is_active,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
        }
    }


@router.put("/agents/{agent_id}", response_model=AgentUpdateResponse)
def update_agent(
    agent_id: int,
    payload: AgentUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an agent."""
    manager = AgentRunManager(db)
    agent = manager.get_agent(agent_id, user_id=current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if payload.name is not None:
        agent.name = payload.name
    if payload.description is not None:
        agent.description = payload.description
    if payload.system_prompt is not None:
        agent.system_prompt = payload.system_prompt
    if payload.model_id is not None:
        agent.model_id = payload.model_id
    if payload.is_active is not None:
        agent.is_active = payload.is_active
    if payload.tools is not None:
        agent.tools_json = json.dumps(payload.tools) if payload.tools else None

    db.commit()
    db.refresh(agent)
    return {"status": "updated"}


@router.delete("/agents/{agent_id}", response_model=dict)
def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an agent."""
    manager = AgentRunManager(db)
    agent = manager.get_agent(agent_id, user_id=current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    active_runs = db.query(AgentRun).filter(AgentRun.agent_id == agent_id, AgentRun.status == "running").all()
    if active_runs:
        raise HTTPException(status_code=409, detail="Cannot delete agent with active runs")
    db.delete(agent)
    db.commit()
    return {"status": "deleted"}
