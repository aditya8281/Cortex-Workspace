"""Sync endpoint schemas."""

from __future__ import annotations

from pydantic import BaseModel


class SyncValidatePathResponse(BaseModel):
    path: str
    resolved_path: str
    exists: bool


class SyncStopResponse(BaseModel):
    status: str
    repo_path: str
