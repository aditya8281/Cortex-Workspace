"""Context rules, state, and events endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.awareness.context import (
    ContextEventCreate,
    ContextEventResponse,
    ContextRuleCreate,
    ContextRuleResponse,
    ContextStateResponse,
)
from backend.app.services.awareness.context_engine import ContextEngineService

router = APIRouter(prefix="/context", tags=["awareness-context"])


# ── Rules ──────────────────────────────────────────────────────────────────


@router.post("/rules", response_model=ContextRuleResponse)
def create_rule(
    body: ContextRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new context rule."""
    svc = ContextEngineService(db)
    return svc.create_rule(
        current_user.id,
        body.name,
        body.rule_type,
        body.description,
        body.conditions,
        body.actions,
        body.priority,
    )


@router.get("/rules", response_model=list[ContextRuleResponse])
def get_rules(
    rule_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get context rules, optionally filtered by type."""
    svc = ContextEngineService(db)
    return svc.get_rules(current_user.id, rule_type)


@router.put("/rules/{rule_id}", response_model=ContextRuleResponse)
def update_rule(
    rule_id: int,
    name: str | None = None,
    description: str | None = None,
    conditions: dict | None = None,
    actions: dict | None = None,
    priority: int | None = None,
    enabled: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing context rule."""
    svc = ContextEngineService(db)
    try:
        return svc.update_rule(
            rule_id,
            name=name,
            description=description,
            conditions=conditions,
            actions=actions,
            priority=priority,
            enabled=enabled,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/rules/{rule_id}", response_model=dict)
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a context rule."""
    svc = ContextEngineService(db)
    try:
        svc.delete_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"deleted": True}


@router.post("/rules/match", response_model=list[ContextRuleResponse])
def match_rules(
    context: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Match context rules against a given context payload."""
    svc = ContextEngineService(db)
    return svc.match_rules(current_user.id, context)


# ── State ──────────────────────────────────────────────────────────────────


@router.get("/state", response_model=list[ContextStateResponse])
def get_all_state(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all context state entries for the current user."""
    svc = ContextEngineService(db)
    return svc.get_all_states(current_user.id)


@router.get("/state/{state_key}", response_model=ContextStateResponse)
def get_state(
    state_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific context state by key."""
    svc = ContextEngineService(db)
    state = svc.get_state(current_user.id, state_key)
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    return state


@router.put("/state/{state_key}", response_model=ContextStateResponse)
def set_state(
    state_key: str,
    state_value: dict,
    source: str = "system",
    confidence: float = 1.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set or update a context state entry."""
    svc = ContextEngineService(db)
    return svc.set_state(current_user.id, state_key, state_value, source, confidence)


# ── Events ─────────────────────────────────────────────────────────────────


@router.post("/events", response_model=ContextEventResponse)
def log_event(
    body: ContextEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log a context event."""
    svc = ContextEngineService(db)
    return svc.log_event(
        current_user.id,
        body.event_type,
        body.event_data,
        body.source,
        body.relevance_score,
        body.related_rule_id,
    )


@router.get("/events", response_model=list[ContextEventResponse])
def get_events(
    event_type: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get context events, optionally filtered by type."""
    svc = ContextEngineService(db)
    return svc.get_events(current_user.id, event_type, limit)
