"""Awareness domain schemas."""

from backend.app.schemas.awareness.attention import (
    AttentionStatsResponse,
    AttentionTrackerCreate,
    AttentionTrackerListResponse,
    AttentionTrackerResponse,
)
from backend.app.schemas.awareness.context import (
    ContextEventCreate,
    ContextEventResponse,
    ContextRuleCreate,
    ContextRuleResponse,
    ContextStateResponse,
)
from backend.app.schemas.awareness.device import DeviceInfoResponse
from backend.app.schemas.awareness.file_tracker import FileChangeSet, FileIndexList, FileIndexResponse
from backend.app.schemas.awareness.health import HealthCheckResponse, SystemHealthResponse
from backend.app.schemas.awareness.indexing import (
    IndexingConfigInfo,
    IndexingConfigResponse,
    IndexingConfigSaveResponse,
    IndexingPreviewResponse,
)
from backend.app.schemas.awareness.project_detector import ProjectIndexResponse
from backend.app.schemas.awareness.repo_analyzer import RepositoryIndexResponse
from backend.app.schemas.awareness.system_snapshot import (
    SystemSnapshotCreate,
    SystemSnapshotListResponse,
    SystemSnapshotResponse,
)

__all__ = [
    "AttentionStatsResponse",
    "AttentionTrackerCreate",
    "AttentionTrackerListResponse",
    "AttentionTrackerResponse",
    "ContextEventCreate",
    "ContextEventResponse",
    "ContextRuleCreate",
    "ContextRuleResponse",
    "ContextStateResponse",
    "DeviceInfoResponse",
    "FileChangeSet",
    "FileIndexList",
    "FileIndexResponse",
    "HealthCheckResponse",
    "IndexingConfigInfo",
    "IndexingConfigResponse",
    "IndexingConfigSaveResponse",
    "IndexingPreviewResponse",
    "ProjectIndexResponse",
    "RepositoryIndexResponse",
    "SystemHealthResponse",
    "SystemSnapshotCreate",
    "SystemSnapshotListResponse",
    "SystemSnapshotResponse",
]
