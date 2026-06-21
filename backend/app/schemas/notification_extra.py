"""Extra notification schemas for mutation endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class NotificationOkResponse(BaseModel):
    ok: bool


class NotificationMarkReadResponse(BaseModel):
    ok: bool
    marked_read: int | None = None
