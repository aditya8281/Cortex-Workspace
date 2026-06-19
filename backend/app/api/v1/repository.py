"""Repository management API — CRUD, indexing, and graph operations."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.repo_index import RepoIndex
from backend.app.models.user import User
from backend.app.services.graph_builder import GraphBuilder
from backend.app.services.incremental_indexer import IncrementalIndexer
from backend.app.tasks.worker import enqueue_task

logger = logging.getLogger(__name__)

router = APIRouter()


class RepoCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    path: str = Field(min_length=1, max_length=2048)


class RepoUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)


def _serialize_repo(repo: RepoIndex) -> dict:
    return {
        "id": repo.id,
        "user_id": repo.user_id,
        "repo_path": repo.repo_path,
        "repo_name": repo.repo_name,
        "primary_language": repo.primary_language,
        "total_files": repo.total_files,
        "total_chunks": repo.total_chunks,
        "last_indexed_at": repo.last_indexed_at.isoformat() if repo.last_indexed_at else None,
        "status": repo.status,
        "created_at": repo.created_at.isoformat() if repo.created_at else None,
        "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
    }


# ── Repository CRUD ─────────────────────────────────────────────


@router.get("/api/v1/repos")
def list_repos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all repositories for the current user."""
    repos = (
        db.query(RepoIndex)
        .filter((RepoIndex.user_id == current_user.id) | (RepoIndex.user_id.is_(None)))
        .order_by(RepoIndex.updated_at.desc())
        .all()
    )
    return {"repos": [_serialize_repo(r) for r in repos]}


@router.post("/api/v1/repos")
def create_repo(
    payload: RepoCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a new repository for indexing."""
    from pathlib import Path

    path = Path(payload.path).expanduser().resolve()
    if not path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {payload.path}")

    # Check for duplicate path
    existing = db.query(RepoIndex).filter(RepoIndex.repo_path == str(path)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Repository already registered")

    repo = RepoIndex(
        user_id=current_user.id,
        repo_path=str(path),
        repo_name=payload.name,
        status="pending",
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    return {"status": "created", "repo": _serialize_repo(repo)}


@router.get("/api/v1/repos/{repo_id}")
def get_repo(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific repository."""
    repo = db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"repo": _serialize_repo(repo)}


@router.put("/api/v1/repos/{repo_id}")
def update_repo(
    repo_id: int,
    payload: RepoUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update repository metadata."""
    repo = db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if payload.name is not None:
        repo.repo_name = payload.name

    db.commit()
    db.refresh(repo)
    return {"status": "updated", "repo": _serialize_repo(repo)}


@router.delete("/api/v1/repos/{repo_id}")
def delete_repo(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a repository and its indexed data."""
    repo = db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    db.delete(repo)
    db.commit()
    return {"status": "deleted"}


# ── Indexing ────────────────────────────────────────────────────


@router.post("/api/v1/repos/{repo_id}/index")
async def index_repo(
    repo_id: int,
    force: bool = False,
    background: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger repository indexing (default: background task)."""
    repo = db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if background:
        job_id = await enqueue_task("index_repo_task", repo_id, force)
        return {"status": "queued", "job_id": job_id}

    # Synchronous indexing
    try:
        indexer = IncrementalIndexer(db)
        result = indexer.index_repo(repo_id, force=force)
        return {"status": "completed", "result": {
            "files_scanned": result.files_scanned,
            "files_indexed": result.files_indexed,
            "files_skipped": result.files_skipped,
            "files_errors": result.files_errors,
            "chunks_created": result.chunks_created,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/repos/{repo_id}/status")
def index_status(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get indexing status for a repository."""
    repo = db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    from backend.app.models.file_index import IndexedFile

    files = db.query(IndexedFile).filter(IndexedFile.repo_id == repo_id).all()

    return {
        "repo_id": repo_id,
        "status": repo.status,
        "total_files": repo.total_files,
        "total_chunks": repo.total_chunks,
        "indexed_files": len(files),
        "indexed": sum(1 for f in files if f.status == "indexed"),
        "pending": sum(1 for f in files if f.status == "pending"),
        "errors": sum(1 for f in files if f.status == "error"),
        "last_indexed_at": repo.last_indexed_at.isoformat() if repo.last_indexed_at else None,
    }


# ── Graph ───────────────────────────────────────────────────────


@router.post("/api/v1/repos/{repo_id}/graph")
def build_graph(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Build the knowledge graph for a repository."""
    repo = db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    builder = GraphBuilder(db)
    result = builder.build_graph(repo_id)
    return {
        "status": "completed",
        "nodes_created": result.nodes_created,
        "edges_created": result.edges_created,
    }


@router.get("/api/v1/repos/{repo_id}/graph")
def get_graph(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the knowledge graph for a repository."""
    repo = db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    builder = GraphBuilder(db)
    return builder.get_graph(repo_id)


@router.get("/api/v1/repos/{repo_id}/graph/node/{node_id}")
def get_node_context(
    repo_id: int,
    node_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get graph context for a specific node."""
    builder = GraphBuilder(db)
    context = builder.get_node_context(node_id)
    if not context:
        raise HTTPException(status_code=404, detail="Node not found")
    return context
