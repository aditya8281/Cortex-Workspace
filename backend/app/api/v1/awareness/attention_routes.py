"""Attention tracking endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.awareness.attention import (
    AttentionStatsResponse,
    AttentionTrackerCreate,
    AttentionTrackerListResponse,
    AttentionTrackerResponse,
)
from backend.app.services.awareness.attention_service import AttentionService

router = APIRouter(prefix="/attention", tags=["awareness-attention"])


@router.post("/session", response_model=AttentionTrackerResponse)
def start_session(
    body: AttentionTrackerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new attention tracking session."""
    svc = AttentionService(db)
    return svc.start_session(
        current_user.id, body.session_type, body.task_description
    )


@router.post("/session/{session_id}/end", response_model=AttentionTrackerResponse)
def end_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """End an attention tracking session."""
    svc = AttentionService(db)
    try:
        return svc.end_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/session/{session_id}/focus", response_model=AttentionTrackerResponse)
def update_focus(
    session_id: int,
    focus_score: float,
    distraction_count: int | None = None,
    switch_count: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update focus metrics for an attention tracking session."""
    svc = AttentionService(db)
    try:
        return svc.update_focus(
            session_id, focus_score, distraction_count, switch_count
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions", response_model=AttentionTrackerListResponse)
def get_sessions(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get attention tracking sessions for the current user."""
    svc = AttentionService(db)
    sessions = svc.get_sessions(current_user.id, limit)
    return {"sessions": sessions, "total": len(sessions)}


@router.get("/stats", response_model=AttentionStatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregated attention statistics for the current user."""
    svc = AttentionService(db)
    return svc.get_stats(current_user.id)
