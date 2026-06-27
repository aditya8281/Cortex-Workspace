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
    will_index: int = 0
    excluded_by_directory: int = 0
    excluded_by_pattern: int = 0
    excluded_by_size: int = 0
