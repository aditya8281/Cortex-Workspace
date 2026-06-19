"""Notification schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    read: bool
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at", mode="before")
    @classmethod
    def _serialize_datetime(cls, v: Any) -> str | None:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    unread_count: int
