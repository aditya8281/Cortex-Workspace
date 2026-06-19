"""Agent API — CRUD, runs, steps, and feedback."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.agents.run_manager import AgentRunManager
from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User

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


class RunCreatePayload(BaseModel):
    agent_id: int
    input: str = Field(min_length=1)


class FeedbackPayload(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


# ── Agent CRUD ──────────────────────────────────────────────────


@router.get("/api/v1/agents")
def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agents."""
    manager = AgentRunManager(db)
    agents = manager.list_agents()
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


@router.post("/api/v1/agents")
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
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/v1/agents/{agent_id}")
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific agent."""
    manager = AgentRunManager(db)
    agent = manager.get_agent(agent_id)
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


@router.put("/api/v1/agents/{agent_id}")
def update_agent(
    agent_id: int,
    payload: AgentUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an agent."""
    manager = AgentRunManager(db)
    agent = manager.get_agent(agent_id)
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

    db.commit()
    db.refresh(agent)
    return {"status": "updated"}


@router.delete("/api/v1/agents/{agent_id}")
def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an agent."""
    manager = AgentRunManager(db)
    agent = manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
    return {"status": "deleted"}


# ── Runs ────────────────────────────────────────────────────────


@router.post("/api/v1/agents/runs")
async def create_run(
    payload: RunCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create and execute an agent run."""
    manager = AgentRunManager(db)
    try:
        run = await manager.run_agent(
            agent_id=payload.agent_id,
            user_id=current_user.id,
            input_text=payload.input,
        )
        return {"status": "completed", "run": manager.serialize_run(run)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/agents/runs")
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


@router.get("/api/v1/agents/runs/{run_id}")
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

    steps = manager.get_run_steps(run_id)
    return {
        "run": manager.serialize_run(run),
        "steps": [manager.serialize_step(s) for s in steps],
    }


@router.get("/api/v1/agents/runs/{run_id}/steps")
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

    steps = manager.get_run_steps(run_id)
    return {"steps": [manager.serialize_step(s) for s in steps]}


# ── Feedback ────────────────────────────────────────────────────


@router.post("/api/v1/agents/runs/{run_id}/feedback")
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/v1/agents/runs/{run_id}/feedback")
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
