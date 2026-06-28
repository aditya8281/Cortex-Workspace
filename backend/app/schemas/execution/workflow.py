"""Workflow schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    name: str = Field(..., description="Workflow name")
    description: str | None = None
    steps: list[dict[str, Any]] = Field(..., description="Step definitions")


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    steps: list[dict[str, Any]] | None = None
    status: str | None = None
    current_step: int | None = None


class WorkflowResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: str | None = None
    steps: list[dict[str, Any]]
    status: str
    current_step: int
    created_at: datetime
    updated_at: datetime | None = None
    last_run: datetime | None = None
    last_run_status: str | None = None
    run_count: int
    total_duration_ms: int | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class WorkflowListResponse(BaseModel):
    items: list[WorkflowResponse]
    total: int
