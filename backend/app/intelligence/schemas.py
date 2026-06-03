from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SyncStatusResponse(BaseModel):
    last_sync_time: str | None = None
    last_sync_status: str | None = None
    files_indexed: int = 0
    repositories_indexed: int = 0
    memory_updates: int = 0
    active_sync_id: int | None = None
    active_sync_status: str | None = None
    progress_message: str | None = None
    discovery_roots: list[str] = Field(default_factory=list)
    tracked_files: int = 0


class SyncRunResponse(BaseModel):
    id: int
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    files_indexed: int
    files_added: int
    files_modified: int
    files_removed: int
    repositories_indexed: int
    memory_updates: int
    progress_message: str | None = None
    result_summary: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AutomationSettingsResponse(BaseModel):
    automation_level: str
    trusted_categories: list[str]
    observer_enabled: bool


class AutomationSettingsUpdate(BaseModel):
    automation_level: str | None = None
    trusted_categories: list[str] | None = None
    observer_enabled: bool | None = None


class ExclusionConfigResponse(BaseModel):
    ignored_dir_names: list[str]
    ignored_path_prefixes: list[str]
    index_extensions: list[str]
    max_file_bytes: int


class ProactiveNotificationResponse(BaseModel):
    id: int
    priority: str
    title: str
    message: str
    action_type: str | None = None
    action_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class SystemActionPlanRequest(BaseModel):
    action_type: str
    description: str
    affected_paths: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    category: str | None = None


class KnowledgeSearchResponse(BaseModel):
    results: list[dict[str, Any]]
