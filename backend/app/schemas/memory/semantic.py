"""Semantic memory Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SemanticMemoryCreate(BaseModel):
    """Schema for creating a new semantic memory."""

    content: str = Field(
        ..., min_length=1, max_length=10000, description="The fact/knowledge"
    )
    category: str | None = Field(
        None, max_length=100, description="Category: preference, fact, concept, rule"
    )
    source: str | None = Field(
        None, max_length=200, description="Where this knowledge came from"
    )

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str | None) -> str | None:
        """Normalize category to lowercase with underscores."""
        if v is not None:
            v = " ".join(v.strip().split()).lower().replace(" ", "_").replace("-", "_")
        return v


class SemanticMemoryUpdate(BaseModel):
    """Schema for updating a semantic memory."""

    content: str | None = Field(None, min_length=1, max_length=10000)
    category: str | None = Field(None, max_length=100)
    source: str | None = Field(None, max_length=200)
    confidence: float | None = Field(None, ge=0.0, le=1.0)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str | None) -> str | None:
        if v is not None:
            v = " ".join(v.strip().split()).lower().replace(" ", "_").replace("-", "_")
        return v


class SemanticMemoryResponse(BaseModel):
    """Schema for returning a semantic memory."""

    id: int
    user_id: int
    content: str
    category: str | None
    confidence: float
    source: str | None
    access_count: int
    last_accessed: datetime | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class SemanticMemoryList(BaseModel):
    """Paginated list of semantic memories."""

    memories: list[SemanticMemoryResponse]
    total: int
    page: int = 1
    page_size: int = 10
