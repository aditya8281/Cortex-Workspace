"""Awareness domain schemas."""

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

__all__ = [
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
]
