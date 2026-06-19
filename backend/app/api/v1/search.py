"""Unified search API — code + memory semantic search."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.cross_file_search import CrossFileSearch
from backend.app.services.memory_manager import MemoryManager

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    repo_id: int | None = None
    node_type: str | None = None
    language: str | None = None
    max_results: int = Field(default=10, ge=1, le=50)


@router.post("/search")
def unified_search(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unified search across memories and indexed code."""
    results: list[dict] = []
    seen: set[str] = set()

    # Code search (if there are indexed repos)
    try:
        code_search = CrossFileSearch(db)
        code_results = code_search.search(
            query=payload.query,
            repo_id=payload.repo_id,
            node_type=payload.node_type,
            language=payload.language,
            limit=payload.max_results,
        )
        for r in code_results:
            key = f"code:{r.get('chunk_id')}"
            if key not in seen:
                results.append({"type": "code", **r})
                seen.add(key)
    except Exception:
        pass  # Code search may fail if no repos indexed

    # Memory search
    try:
        memory_search = MemoryManager(db)
        memory_results = memory_search.search(
            query=payload.query,
            user_id=current_user.id,
            limit=payload.max_results,
        )
        for r in memory_results:
            entry = r.get("entry")
            key = f"memory:{entry.get('id') if entry else 'null'}"
            if key not in seen:
                results.append({"type": "memory", **r})
                seen.add(key)
    except Exception:
        pass  # Memory search may fail

    # Sort by score descending
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "query": payload.query,
        "total": len(results[:payload.max_results]),
        "results": results[:payload.max_results],
    }


@router.get("/search")
def unified_search_get(
    q: str = Query(min_length=1, max_length=1000),
    repo_id: int | None = None,
    node_type: str | None = None,
    language: str | None = None,
    max_results: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET variant of unified search."""
    payload = SearchRequest(
        query=q, repo_id=repo_id, node_type=node_type,
        language=language, max_results=max_results,
    )
    return unified_search(payload, db, current_user)
