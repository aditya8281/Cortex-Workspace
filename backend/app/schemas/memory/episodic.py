"""Episodic memory Pydantic schemas."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class EpisodicMemoryCreate(BaseModel):
    """Schema for creating a new episodic memory."""

    content: str = Field(..., min_length=1, max_length=10000, description="What happened")
    context: dict | None = Field(
        None, description="Provenance: source, trigger, environment"
    )
    emotion: str | None = Field(None, max_length=50, description="Emotional state tag")
    importance: float = Field(0.5, ge=0.0, le=1.0, description="Intrinsic importance 0.0-1.0")

    @field_validator("content")
    @classmethod
    def content_must_not_contain_secrets(cls, v: str) -> str:
        """Reject content that looks like secrets."""
        secret_patterns = [
            r"(?i)api[_-]?key\s*[:=]\s*\S+",
            r"(?i)password\s*[:=]\s*\S+",
            r"(?i)token\s*[:=]\s*\S+",
            r"sk-[a-zA-Z0-9]{20,}",
        ]
        for pattern in secret_patterns:
            if re.search(pattern, v):
                raise ValueError(
                    "Content must not contain API keys, passwords, or tokens"
                )
        return v


class EpisodicMemoryUpdate(BaseModel):
    """Schema for updating an episodic memory."""

    content: str | None = Field(None, min_length=1, max_length=10000)
    context: dict | None = None
    emotion: str | None = Field(None, max_length=50)
    importance: float | None = Field(None, ge=0.0, le=1.0)


class EpisodicMemoryResponse(BaseModel):
    """Schema for returning an episodic memory."""

    id: int
    user_id: int
    content: str
    context: dict | None
    emotion: str | None
    importance: float
    confidence: float
    access_count: int
    last_accessed: datetime | None
    created_at: datetime
    updated_at: datetime | None
    recency_score: float

    model_config = {"from_attributes": True}


class EpisodicMemoryList(BaseModel):
    """Paginated list of episodic memories."""

    memories: list[EpisodicMemoryResponse]
    total: int
    page: int = 1
    page_size: int = 10
