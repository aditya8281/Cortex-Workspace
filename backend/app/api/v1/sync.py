from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.app.core.config import settings
from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.sync import SyncStopResponse, SyncValidatePathResponse
from backend.app.services.file_watcher_v2 import get_file_watcher_v2
from backend.app.tasks.worker import enqueue_task

router = APIRouter()

# ── Platform-aware default sync paths ─────────────────────────────────
# These are the standard Linux XDG user directories. On other platforms
# (macOS, Windows) different paths are used. Only paths that actually
# exist on disk will be enabled by default.


def _get_platform_default_paths() -> list[dict[str, Any]]:
    """Return default sync paths appropriate for the current OS."""
    import sys

    paths = []

    # Home directory — always first, always enabled if exists
    paths.append({"label": "Home Directory", "path": "~", "enabled": True})

    if sys.platform == "linux" or sys.platform.startswith("linux"):
        # Linux XDG user directories
        paths += [
            {"label": "Desktop", "path": "~/Desktop", "enabled": True},
            {"label": "Downloads", "path": "~/Downloads", "enabled": True},
            {"label": "Documents", "path": "~/Documents", "enabled": True},
            {"label": "Music", "path": "~/Music", "enabled": False},
            {"label": "Pictures", "path": "~/Pictures", "enabled": False},
            {"label": "Videos", "path": "~/Videos", "enabled": False},
            {"label": "Public", "path": "~/Public", "enabled": False},
            {"label": "Templates", "path": "~/Templates", "enabled": False},
            # Common Linux dev directories (auto-enabled if they exist)
            {"label": "Projects", "path": "~/Projects", "enabled": True},
            {"label": "Workspace", "path": "~/workspace", "enabled": True},
            {"label": "Source", "path": "~/src", "enabled": True},
            {"label": "Dev", "path": "~/dev", "enabled": True},
            {"label": "Code", "path": "~/code", "enabled": True},
        ]
    elif sys.platform == "darwin":
        # macOS standard directories
        paths += [
            {"label": "Desktop", "path": "~/Desktop", "enabled": True},
            {"label": "Downloads", "path": "~/Downloads", "enabled": True},
            {"label": "Documents", "path": "~/Documents", "enabled": True},
            {"label": "Music", "path": "~/Music", "enabled": False},
            {"label": "Pictures", "path": "~/Pictures", "enabled": False},
            {"label": "Movies", "path": "~/Movies", "enabled": False},
            {"label": "Applications", "path": "~/Applications", "enabled": False},
            {"label": "Projects", "path": "~/Projects", "enabled": True},
            {"label": "Workspace", "path": "~/workspace", "enabled": True},
        ]
    elif sys.platform == "win32" or sys.platform == "cygwin":
        # Windows standard directories
        userprofile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        paths += [
            {"label": "Desktop", "path": os.path.join(userprofile, "Desktop"), "enabled": True},
            {"label": "Downloads", "path": os.path.join(userprofile, "Downloads"), "enabled": True},
            {"label": "Documents", "path": os.path.join(userprofile, "Documents"), "enabled": True},
            {"label": "Music", "path": os.path.join(userprofile, "Music"), "enabled": False},
            {"label": "Pictures", "path": os.path.join(userprofile, "Pictures"), "enabled": False},
            {"label": "Videos", "path": os.path.join(userprofile, "Videos"), "enabled": False},
            {"label": "Projects", "path": os.path.join(userprofile, "Projects"), "enabled": True},
            {"label": "Source", "path": os.path.join(userprofile, "source"), "enabled": True},
        ]
    else:
        # Fallback for unknown platforms (still try common dirs)
        paths += [
            {"label": "Desktop", "path": "~/Desktop", "enabled": True},
            {"label": "Downloads", "path": "~/Downloads", "enabled": True},
            {"label": "Documents", "path": "~/Documents", "enabled": True},
        ]

    return paths


def _get_default_sync_paths() -> list[dict[str, Any]]:
    """Return default sync paths with resolved absolute paths.

    Only directories that actually exist on disk will be enabled.
    Platform-specific paths are auto-detected.
    """
    default_paths = _get_platform_default_paths()
    resolved = []
    for p in default_paths:
        resolved_path = os.path.expanduser(p["path"])
        exists = os.path.isdir(resolved_path)
        # Only enable if it exists AND is marked as enabled
        resolved.append(
            {
                "label": p["label"],
                "path": resolved_path,
                "enabled": p["enabled"] and exists,
                "exists": exists,
            }
        )
    return resolved


# Directories to exclude from sync by default
DEFAULT_EXCLUDE_DIRS = [
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    "dist",
    "build",
    ".next",
    "target",
    ".cache",
    "tmp",
    ".local/share",
    ".npm",
    ".cargo",
    ".rustup",
]

# Available embedding models with technique descriptions
EMBEDDING_MODELS = [
    {
        "value": "nomic-embed-text",
        "label": "Nomic Embed Text",
        "technique": "ONNX / Ollama",
        "dimensions": 768,
        "description": "Fast, lightweight embeddings. Good balance of speed and quality.",
        "speed": "fast",
    },
    {
        "value": "mxbai-embed-large",
        "label": "MXBai Embed Large",
        "technique": "ONNX / Ollama",
        "dimensions": 1024,
        "description": "High-quality embeddings with larger dimension. Best accuracy.",
        "speed": "medium",
    },
    {
        "value": "all-minilm-l6-v2",
        "label": "All MiniLM-L6-v2",
        "technique": "Sentence Transformers",
        "dimensions": 384,
        "description": "Classic sentence transformer. Fast and widely compatible.",
        "speed": "fast",
    },
    {
        "value": "bge-small-en-v1.5",
        "label": "BGE Small English",
        "technique": "Sentence Transformers",
        "dimensions": 384,
        "description": "BAAI embedding model. Strong retrieval performance.",
        "speed": "fast",
    },
    {
        "value": "bge-base-en-v1.5",
        "label": "BGE Base English",
        "technique": "Sentence Transformers",
        "dimensions": 768,
        "description": "BAAI base model. Good quality for general use.",
        "speed": "medium",
    },
    {
        "value": "bge-large-en-v1.5",
        "label": "BGE Large English",
        "technique": "Sentence Transformers",
        "dimensions": 1024,
        "description": "BAAI large model. Highest quality embeddings.",
        "speed": "slow",
    },
    {
        "value": "e5-small-v2",
        "label": "E5 Small v2",
        "technique": "Sentence Transformers",
        "dimensions": 384,
        "description": "Microsoft E5 model. Excellent for semantic search.",
        "speed": "fast",
    },
    {
        "value": "e5-base-v2",
        "label": "E5 Base v2",
        "technique": "Sentence Transformers",
        "dimensions": 768,
        "description": "Microsoft E5 base. Balanced quality and speed.",
        "speed": "medium",
    },
    {
        "value": "gte-small",
        "label": "GTE Small",
        "technique": "Sentence Transformers",
        "dimensions": 384,
        "description": "Alibaba GTE model. Strong multilingual support.",
        "speed": "fast",
    },
    {
        "value": "mock",
        "label": "Mock (Testing)",
        "technique": "Hash-based",
        "dimensions": 768,
        "description": "Deterministic mock embeddings for testing. Not semantically meaningful.",
        "speed": "instant",
    },
]


class SyncStartPayload(BaseModel):
    repo_path: str = Field(min_length=1, max_length=4096)
    embedding_model: str | None = None
    exclude_dirs: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)


class SyncValidatePathPayload(BaseModel):
    path: str = Field(min_length=1, max_length=4096)


class SyncStopPayload(BaseModel):
    repo_path: str = Field(min_length=1, max_length=4096)


class SyncDefaultsResponse(BaseModel):
    default_paths: list[dict[str, Any]]
    exclude_dirs: list[str]
    embedding_models: list[dict[str, Any]]


class SyncStatusResponse(BaseModel):
    watching: int
    pending_changes: int
    indexed_files: int
    errors: int
    status: str
    last_sync: str | None
    watched_paths: list[dict[str, Any]]


class SyncStartResponse(BaseModel):
    status: str
    repo_path: str
    embedding_model: str
    initial_scan_job_id: str | None


class SyncJobResponse(BaseModel):
    job_id: str
    repo_path: str
    job_type: str
    status: str
    progress: int
    total: int | None
    result: dict[str, Any] | None
    error: str | None
    created_at: str
    updated_at: str


@router.get("/sync/defaults", response_model=SyncDefaultsResponse)
async def get_sync_defaults(
    current_user: User = Depends(get_current_user),
):
    """Return default sync paths, exclude dirs, and available embedding models."""
    del current_user
    return SyncDefaultsResponse(
        default_paths=_get_default_sync_paths(),
        exclude_dirs=DEFAULT_EXCLUDE_DIRS,
        embedding_models=EMBEDDING_MODELS,
    )


@router.post("/sync/start", response_model=SyncStartResponse)
async def start_sync(
    payload: SyncStartPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.app.core.system_paths import get_blocked_system_paths
    from backend.app.models.repo_index import RepoIndex
    from backend.app.models.sync_state import SyncState

    repo_path = str(Path(payload.repo_path).expanduser().resolve())

    for blocked in get_blocked_system_paths():
        if repo_path.startswith(blocked):
            raise HTTPException(status_code=400, detail=f"Cannot sync system path: {blocked}")

    if not Path(repo_path).is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {repo_path}")

    embedding_model = payload.embedding_model or settings.EMBEDDING_MODEL_NAME

    repo = db.query(RepoIndex).filter(RepoIndex.repo_path == repo_path).first()
    if not repo:
        repo = RepoIndex(
            user_id=current_user.id,
            repo_path=repo_path,
            repo_name=Path(repo_path).name,
            status="pending",
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)

    existing_state = (
        db.query(SyncState)
        .filter(
            SyncState.user_id == current_user.id,
            SyncState.repo_path == repo_path,
        )
        .first()
    )
    if not existing_state:
        db.add(
            SyncState(
                user_id=current_user.id,
                repo_path=repo_path,
                repo_id=repo.id,
                status="active",
                config_json={"embedding_model": embedding_model},
            )
        )
        db.commit()

    watcher = get_file_watcher_v2()
    watcher.watch(repo_path)

    try:
        job_id = await enqueue_task("scan_repo_task", repo_path, current_user.id)
    except Exception as e:
        logger.error("Failed to enqueue scan task for %s: %s", repo_path, e)
        raise HTTPException(status_code=500, detail="Failed to start scan task")

    return SyncStartResponse(
        status="started",
        repo_path=repo_path,
        embedding_model=embedding_model,
        initial_scan_job_id=job_id,
    )


@router.post("/sync/validate-path", response_model=SyncValidatePathResponse)
async def validate_sync_path(
    payload: SyncValidatePathPayload,
    current_user: User = Depends(get_current_user),
):
    """Check if a path exists and is a directory. Returns resolved path info."""
    resolved_path = str(Path(payload.path).expanduser().resolve())
    exists = Path(resolved_path).is_dir()
    return {
        "path": payload.path,
        "resolved_path": resolved_path,
        "exists": exists,
    }


@router.post("/sync/stop", response_model=SyncStopResponse)
async def stop_sync(
    payload: SyncStopPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.app.models.sync_state import SyncState

    repo_path = str(Path(payload.repo_path).expanduser().resolve())
    watcher = get_file_watcher_v2()
    if not watcher.unwatch(repo_path):
        raise HTTPException(status_code=404, detail="Path is not being watched")

    state = (
        db.query(SyncState)
        .filter(
            SyncState.user_id == current_user.id,
            SyncState.repo_path == repo_path,
        )
        .first()
    )
    if state:
        state.status = "stopped"
        db.commit()

    return {"status": "stopped", "repo_path": repo_path}


@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.app.models.sync_state import SyncState

    watcher = get_file_watcher_v2()
    user_states = db.query(SyncState).filter(SyncState.user_id == current_user.id).all()
    watched_paths = [
        {
            "path": s.repo_path,
            "repo_id": s.repo_id,
            "embedding_model": (s.config_json or {}).get("embedding_model", ""),
            "sync_enabled": s.status == "active",
            "initial_scan_job_id": None,
            "initial_scan_status": s.status,
        }
        for s in user_states
    ]

    return SyncStatusResponse(
        watching=watcher.watched_count,
        pending_changes=0,
        indexed_files=0,
        errors=0,
        status="watching" if watcher.is_running else "idle",
        last_sync=None,
        watched_paths=watched_paths,
    )


@router.get("/sync/jobs", response_model=list[SyncJobResponse])
async def get_sync_jobs(
    current_user: User = Depends(get_current_user),
):
    return []


@router.get("/sync/jobs/{job_id}", response_model=SyncJobResponse)
async def get_sync_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    raise HTTPException(status_code=404, detail="Job not found")
