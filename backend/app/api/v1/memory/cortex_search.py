"""Cross-type memory search and forgetting API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.services.memory.decay import ForgettingService
from backend.app.services.memory.memory_search import MemorySearchService

router = APIRouter(prefix="/cortex-search", tags=["memory-cortex-search"])


@router.get("")
def search_all_memories(
    query: str = Query(..., min_length=1, max_length=200),
    memory_type: str | None = Query(None, pattern=r"^(episodic|semantic|working)$"),
    limit: int = Query(10, ge=1, le=50),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Search across all memory types with multi-signal scoring."""
    service = MemorySearchService(db)
    results = service.search(current_user.id, query, memory_type, limit, min_score)
    return {"results": results, "query": query, "count": len(results)}


@router.get("/related")
def get_related_memories(
    memory_type: str = Query(..., pattern=r"^(episodic|semantic)$"),
    memory_id: int = Query(..., gt=0),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get memories related via graph connections."""
    service = MemorySearchService(db)
    results = service.get_related_memories(current_user.id, memory_type, memory_id, limit)
    return {"related": results, "count": len(results)}


@router.get("/importance")
def search_by_importance(
    min_importance: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Search memories by importance threshold."""
    service = MemorySearchService(db)
    return service.search_by_importance(current_user.id, min_importance, limit)


@router.get("/recency")
def search_by_recency(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Search memories by most recent."""
    service = MemorySearchService(db)
    return service.search_by_recency(current_user.id, limit)


forget_router = APIRouter(prefix="/forget", tags=["memory-forget"])


@forget_router.post("")
def apply_forgetting(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Apply forgetting decay to all memories."""
    service = ForgettingService(db)
    return service.apply_decay(current_user.id)


@forget_router.get("/stats")
def get_forgetting_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get forgetting statistics."""
    service = ForgettingService(db)
    return service.get_forgetting_stats(current_user.id)
