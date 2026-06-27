"""File index Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FileIndexResponse(BaseModel):
    """Schema for returning a file index entry."""

    id: int
    user_id: int
    file_path: str
    file_name: str
    file_extension: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    last_modified: datetime | None = None
    indexed_at: datetime
    content_hash: str | None = None
    parent_directory: str | None = None

    model_config = {"from_attributes": True}


class FileIndexList(BaseModel):
    """Paginated list of file indices."""

    files: list[FileIndexResponse]
    total: int
    directory: str | None = None


class FileChangeSet(BaseModel):
    """Set of detected file changes."""

    created: list[FileIndexResponse]
    modified: list[FileIndexResponse]
    deleted: list[str]  # File paths
    scan_time_ms: int
