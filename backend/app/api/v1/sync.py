from __future__ import annotations

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


class SyncStartPayload(BaseModel):
    repo_path: str = Field(min_length=1, max_length=4096)
    embedding_model: str | None = None


class SyncStopPayload(BaseModel):
    repo_path: str = Field(min_length=1, max_length=4096)


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
