from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.db import get_current_user
from backend.app.models.user import User
from backend.app.services.file_watcher import SyncJob, file_watcher
from backend.app.tasks.worker import enqueue_task

router = APIRouter()

# Default home directories to sync
DEFAULT_SYNC_PATHS = [
    {"label": "Home Directory", "path": "~", "enabled": True},
    {"label": "Desktop", "path": "~/Desktop", "enabled": True},
    {"label": "Downloads", "path": "~/Downloads", "enabled": True},
    {"label": "Documents", "path": "~/Documents", "enabled": True},
]

# Directories to exclude from sync by default
DEFAULT_EXCLUDE_DIRS = [
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".next", "target", ".cache", "tmp",
    ".local/share", ".npm", ".cargo", ".rustup",
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


def _get_default_sync_paths() -> list[dict[str, Any]]:
    """Return default sync paths with resolved absolute paths."""
    home = os.path.expanduser("~")
    resolved = []
    for p in DEFAULT_SYNC_PATHS:
        resolved_path = os.path.expanduser(p["path"])
        exists = os.path.isdir(resolved_path)
        resolved.append({
            "label": p["label"],
            "path": resolved_path,
            "enabled": p["enabled"] and exists,
            "exists": exists,
        })
    return resolved


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


class SyncStartPayload(BaseModel):
    repo_path: str = Field(min_length=1, max_length=4096)
    embedding_model: str | None = None
    exclude_dirs: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)


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


@router.post("/sync/start", response_model=SyncStartResponse)
async def start_sync(
    payload: SyncStartPayload,
    current_user: User = Depends(get_current_user),
):
    from backend.app.db.session import SessionLocal
    from backend.app.models.repo_index import RepoIndex

    repo_path = str(Path(payload.repo_path).expanduser().resolve())
    if not Path(repo_path).is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {repo_path}")

    embedding_model = payload.embedding_model or settings.EMBEDDING_MODEL_NAME

    db = SessionLocal()
    try:
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

        file_watcher.watch(repo_path, repo.id, embedding_model)

        job_id = await enqueue_task("scan_repo_task", repo_path, current_user.id)

        job = SyncJob(
            job_id=job_id or "unknown",
            repo_path=repo_path,
            job_type="scan",
            status="pending",
        )
        file_watcher.add_job(job)

        return SyncStartResponse(
            status="started",
            repo_path=repo_path,
            embedding_model=embedding_model,
            initial_scan_job_id=job_id,
        )
    finally:
        db.close()


@router.post("/sync/stop")
async def stop_sync(
    payload: SyncStopPayload,
    current_user: User = Depends(get_current_user),
):
    del current_user
    repo_path = str(Path(payload.repo_path).expanduser().resolve())
    if repo_path not in file_watcher.watched:
        raise HTTPException(status_code=404, detail="Path is not being watched")

    file_watcher.unwatch(repo_path)
    return {"status": "stopped", "repo_path": repo_path}


@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    current_user: User = Depends(get_current_user),
):
    del current_user
    state = file_watcher.sync_state
    return SyncStatusResponse(
        watching=state["watching"],
        pending_changes=state["pending"],
        indexed_files=state["indexed"],
        errors=state["errors"],
        status=state["status"],
        last_sync=state["last_sync"],
        watched_paths=state.get("watched_paths", []),
    )


@router.get("/sync/jobs", response_model=list[SyncJobResponse])
async def get_sync_jobs(
    current_user: User = Depends(get_current_user),
):
    del current_user
    jobs = file_watcher.get_all_jobs()
    return [
        SyncJobResponse(
            job_id=j.job_id,
            repo_path=j.repo_path,
            job_type=j.job_type,
            status=j.status,
            progress=j.progress,
            total=j.total,
            result=j.result,
            error=j.error,
            created_at=j.created_at.isoformat(),
            updated_at=j.updated_at.isoformat(),
        )
        for j in jobs
        if j.job_type in ("scan", "index")
    ]


@router.get("/sync/jobs/{job_id}", response_model=SyncJobResponse)
async def get_sync_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    del current_user
    job = file_watcher.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return SyncJobResponse(
        job_id=job.job_id,
        repo_path=job.repo_path,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        total=job.total,
        result=job.result,
        error=job.error,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )
