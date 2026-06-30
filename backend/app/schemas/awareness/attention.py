"""Attention tracker Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AttentionTrackerCreate(BaseModel):
    """Schema for creating an attention tracker session."""

    session_type: Literal["general", "coding", "research", "review"] = "general"
    task_description: str | None = None
    focus_score: float = 0.0
    distraction_count: int = 0
    switch_count: int = 0
    duration_seconds: float = 0.0
    productive_seconds: float = 0.0
    active_apps: list[str] = []
    context_switches: list[dict] = []


class AttentionTrackerResponse(AttentionTrackerCreate):
    """Schema for returning an attention tracker session."""

    id: int
    user_id: int
    started_at: datetime
    ended_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AttentionTrackerListResponse(BaseModel):
    """Schema for returning a list of attention tracker sessions."""

    sessions: list[AttentionTrackerResponse]
    total: int


class AttentionStatsResponse(BaseModel):
    """Schema for returning attention statistics summary."""

    total_sessions: int
    avg_focus_score: float
    avg_duration: float
    total_productive_time: float
    sessions_by_type: dict[str, int]
