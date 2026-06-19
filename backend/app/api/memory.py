"""Memory API with CRUD operations and semantic search."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.memory_manager import MemoryManager
from backend.app.tasks.worker import enqueue_task

router = APIRouter()


class MemoryCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1)
    category: str = Field(default="note", min_length=1, max_length=64)
    source_path: str | None = Field(default=None, max_length=1024)
    tags: list[str] | None = None


class MemoryUpdatePayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=512)
    content: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, min_length=1, max_length=64)
    tags: list[str] | None = None


class MemorySearchPayload(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    category: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


@router.get("/api/v1/memory")
def list_memory(
    limit: int = 24,
    offset: int = 0,
    category: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List knowledge entries with pagination and category filtering."""
    manager = MemoryManager(db)
    entries, total, categories = manager.list_entries(
        user_id=current_user.id,
        category=category,
        limit=min(max(limit, 1), 100),
        offset=max(offset, 0),
    )

    return {
        "total": total,
        "count": len(entries),
        "offset": offset,
        "limit": limit,
        "categories": categories,
        "entries": [manager._serialize(e) for e in entries],
    }


@router.post("/api/v1/memory")
def create_memory(
    payload: MemoryCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new knowledge entry with vector embedding."""
    manager = MemoryManager(db)
    entry = manager.create(
        user_id=current_user.id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        source_path=payload.source_path,
        tags=payload.tags,
    )
    return {"status": "created", "entry": manager._serialize(entry)}


@router.get("/api/v1/memory/{entry_id}")
def get_memory(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single knowledge entry by ID."""
    manager = MemoryManager(db)
    entry = manager.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return {"entry": manager._serialize(entry)}


@router.put("/api/v1/memory/{entry_id}")
def update_memory(
    entry_id: int,
    payload: MemoryUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a knowledge entry and re-embed if content changed."""
    manager = MemoryManager(db)
    entry = manager.update(
        entry_id=entry_id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        tags=payload.tags,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return {"status": "updated", "entry": manager._serialize(entry)}


@router.delete("/api/v1/memory/{entry_id}")
def delete_memory(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a knowledge entry and its vector embedding."""
    manager = MemoryManager(db)
    deleted = manager.delete(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return {"status": "deleted"}


@router.post("/api/v1/memory/search")
def search_memory(
    payload: MemorySearchPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Semantic search over knowledge entries using vector similarity."""
    manager = MemoryManager(db)
    results = manager.search(
        query=payload.query,
        user_id=current_user.id,
        category=payload.category,
        limit=payload.limit,
    )
    return {"query": payload.query, "results": results}


class ScanRepoPayload(BaseModel):
    repo_path: str = Field(min_length=1, max_length=2048)


class BulkEmbedPayload(BaseModel):
    entry_ids: list[int] = Field(min_length=1)


@router.post("/api/v1/memory/scan-repo")
async def scan_repo(
    payload: ScanRepoPayload,
    current_user: User = Depends(get_current_user),
):
    """Trigger background repository scanning."""
    job_id = await enqueue_task(
        "scan_repo_task",
        payload.repo_path,
        current_user.id,
    )
    return {"status": "queued", "job_id": job_id}


@router.post("/api/v1/memory/bulk-embed")
async def bulk_embed(
    payload: BulkEmbedPayload,
    current_user: User = Depends(get_current_user),
):
    """Trigger background bulk embedding of memory entries."""
    job_id = await enqueue_task("bulk_embed_task", payload.entry_ids)
    return {"status": "queued", "job_id": job_id}
