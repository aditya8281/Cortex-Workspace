"""Episodic memory API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.memory.episodic import (
    EpisodicMemoryCreate,
    EpisodicMemoryList,
    EpisodicMemoryResponse,
    EpisodicMemoryUpdate,
)
from backend.app.services.memory.episodic import EpisodicMemoryService

router = APIRouter(prefix="/episodic", tags=["memory-episodic"])


@router.post("", response_model=EpisodicMemoryResponse, status_code=201)
def create_episodic_memory(
    data: EpisodicMemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EpisodicMemoryResponse:
    """Create a new episodic memory."""
    service = EpisodicMemoryService(db)
    return EpisodicMemoryResponse.model_validate(service.create(current_user.id, data))


@router.get("", response_model=EpisodicMemoryList)
def list_episodic_memories(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EpisodicMemoryList:
    """List recent episodic memories with pagination."""
    service = EpisodicMemoryService(db)
    memories, total = service.list_recent(current_user.id, limit, offset)
    page = (offset // limit) + 1 if limit > 0 else 1
    return EpisodicMemoryList(
        memories=[EpisodicMemoryResponse.model_validate(m) for m in memories],
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/search")
def search_episodic_memories(
    query: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Search episodic memories by content."""
    service = EpisodicMemoryService(db)
    results = service.search_content(current_user.id, query, limit)
    return {
        "results": [EpisodicMemoryResponse.model_validate(m).model_dump() for m in results],
        "query": query,
        "count": len(results),
    }


@router.get("/{memory_id}", response_model=EpisodicMemoryResponse)
def get_episodic_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EpisodicMemoryResponse:
    """Get a specific episodic memory by ID."""
    service = EpisodicMemoryService(db)
    memory = service.retrieve(current_user.id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return EpisodicMemoryResponse.model_validate(memory)


@router.patch("/{memory_id}", response_model=EpisodicMemoryResponse)
def update_episodic_memory(
    memory_id: int,
    data: EpisodicMemoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EpisodicMemoryResponse:
    """Update an episodic memory (partial update)."""
    service = EpisodicMemoryService(db)
    memory = service.update(current_user.id, memory_id, data)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return EpisodicMemoryResponse.model_validate(memory)


@router.delete("/{memory_id}", status_code=204)
def delete_episodic_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an episodic memory."""
    service = EpisodicMemoryService(db)
    deleted = service.delete(current_user.id, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
