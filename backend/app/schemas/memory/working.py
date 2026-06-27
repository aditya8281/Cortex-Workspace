"""Working memory Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class WorkingMemoryCreate(BaseModel):
    """Schema for adding an item to working memory."""

    session_id: str = Field(..., min_length=1, max_length=100, description="Session UUID")
    content: str = Field(..., min_length=1, max_length=5000, description="Context item")
    slot: str = Field("active", description="Slot: active, buffer, archive")
    priority: int = Field(0, ge=0, le=100, description="Priority 0-100")

    @field_validator("slot")
    @classmethod
    def validate_slot(cls, v: str) -> str:
        valid_slots = {"active", "buffer", "archive"}
        if v not in valid_slots:
            raise ValueError(f"Slot must be one of: {valid_slots}")
        return v


class WorkingMemoryUpdate(BaseModel):
    """Schema for updating a working memory item."""

    content: str | None = Field(None, min_length=1, max_length=5000)
    slot: str | None = None
    priority: int | None = Field(None, ge=0, le=100)

    @field_validator("slot")
    @classmethod
    def validate_slot(cls, v: str | None) -> str | None:
        if v is not None:
            valid_slots = {"active", "buffer", "archive"}
            if v not in valid_slots:
                raise ValueError(f"Slot must be one of: {valid_slots}")
        return v


class WorkingMemoryResponse(BaseModel):
    """Schema for returning a working memory item."""

    id: int
    user_id: int
    session_id: str
    content: str
    slot: str
    priority: int
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class WorkingMemoryList(BaseModel):
    """List of working memory items."""

    memories: list[WorkingMemoryResponse]
    total: int
