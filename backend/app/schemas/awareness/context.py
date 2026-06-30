"""Context rule, state, and event Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ContextRuleCreate(BaseModel):
    """Schema for creating a context rule."""

    name: str
    description: str | None = None
    rule_type: Literal["time", "location", "app", "project", "custom"]
    conditions: dict = {}
    actions: dict = {}
    priority: int = 0
    enabled: bool = True


class ContextRuleResponse(ContextRuleCreate):
    """Schema for returning a context rule."""

    id: int
    user_id: int
    hit_count: int
    last_hit_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContextStateResponse(BaseModel):
    """Schema for returning a context state."""

    id: int
    user_id: int
    state_key: str
    state_value: dict
    source: str
    confidence: float
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContextEventCreate(BaseModel):
    """Schema for creating a context event."""

    event_type: Literal["app_switch", "file_open", "project_change", "rule_match", "custom"]
    event_data: dict = {}
    source: str = "system"
    relevance_score: float = 0.0
    related_rule_id: int | None = None


class ContextEventResponse(ContextEventCreate):
    """Schema for returning a context event."""

    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
