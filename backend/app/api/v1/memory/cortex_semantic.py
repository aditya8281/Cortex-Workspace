"""Semantic memory API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.memory.semantic import (
    SemanticMemoryCreate,
    SemanticMemoryList,
    SemanticMemoryResponse,
    SemanticMemoryUpdate,
)
from backend.app.services.memory.semantic import SemanticMemoryService

router = APIRouter(prefix="/semantic", tags=["memory-semantic"])


@router.post("", response_model=SemanticMemoryResponse, status_code=201)
def create_semantic_memory(
    data: SemanticMemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SemanticMemoryResponse:
    """Create a new semantic memory. Deduplicates identical content."""
    service = SemanticMemoryService(db)
    return service.create(current_user.id, data)


@router.get("", response_model=SemanticMemoryList)
def list_semantic_memories(
    category: str | None = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SemanticMemoryList:
    """List semantic memories, optionally filtered by category."""
    service = SemanticMemoryService(db)
    if category:
        memories = service.list_by_category(current_user.id, category, limit)
        return SemanticMemoryList(
            memories=memories,
            total=len(memories),
        )
    memories, total = service.list_all(current_user.id, limit, offset)
    page = (offset // limit) + 1 if limit > 0 else 1
    return SemanticMemoryList(
        memories=[SemanticMemoryResponse.model_validate(m) for m in memories],
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/categories")
def get_semantic_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Get all categories with counts."""
    service = SemanticMemoryService(db)
    return service.get_categories(current_user.id)


@router.get("/search")
def search_semantic_memories(
    query: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Search semantic memories by content."""
    service = SemanticMemoryService(db)
    results = service.search_content(current_user.id, query, limit)
    return {
        "results": [SemanticMemoryResponse.model_validate(m).model_dump() for m in results],
        "query": query,
        "count": len(results),
    }


@router.get("/{memory_id}", response_model=SemanticMemoryResponse)
def get_semantic_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SemanticMemoryResponse:
    """Get a specific semantic memory."""
    service = SemanticMemoryService(db)
    memory = service.retrieve(current_user.id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.patch("/{memory_id}", response_model=SemanticMemoryResponse)
def update_semantic_memory(
    memory_id: int,
    data: SemanticMemoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SemanticMemoryResponse:
    """Update a semantic memory."""
    service = SemanticMemoryService(db)
    memory = service.update(current_user.id, memory_id, data)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.delete("/{memory_id}", status_code=204)
def delete_semantic_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a semantic memory."""
    service = SemanticMemoryService(db)
    deleted = service.delete(current_user.id, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
