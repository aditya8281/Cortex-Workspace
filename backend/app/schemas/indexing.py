"""Indexing endpoint schemas."""

from __future__ import annotations

from pydantic import BaseModel


class IndexingConfigInfo(BaseModel):
    id: int
    name: str
    include_paths: list[str]
    exclude_paths: list[str]
    include_patterns: list[str]
    exclude_patterns: list[str]
    max_file_size_bytes: int
    follow_symlinks: bool
    sync_enabled: bool
    sync_interval_seconds: int
    priority: int


class IndexingConfigResponse(BaseModel):
    config: IndexingConfigInfo | None = None
    defaults: bool = False


class IndexingConfigSaveResponse(BaseModel):
    status: str


class IndexingPreviewResponse(BaseModel):
    total_files: int = 0
    included_files: int = 0
    excluded_files: int = 0
    by_extension: dict[str, int] = {}
