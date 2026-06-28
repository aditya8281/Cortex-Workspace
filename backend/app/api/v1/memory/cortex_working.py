"""Working memory API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.memory.working import (
    WorkingMemoryCreate,
    WorkingMemoryList,
    WorkingMemoryResponse,
)
from backend.app.services.memory.working import WorkingMemoryService

router = APIRouter(prefix="/working", tags=["memory-working"])


@router.post("", response_model=WorkingMemoryResponse, status_code=201)
def add_working_memory(
    data: WorkingMemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkingMemoryResponse:
    """Add an item to working memory."""
    service = WorkingMemoryService(db)
    return WorkingMemoryResponse.model_validate(service.add(
        user_id=current_user.id,
        session_id=data.session_id,
        content=data.content,
        slot=data.slot,
        priority=data.priority,
    ))


@router.get("", response_model=WorkingMemoryList)
def get_working_memory(
    session_id: str = Query(..., min_length=1, max_length=100),
    slot: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkingMemoryList:
    """Get working memory items for a session."""
    service = WorkingMemoryService(db)
    if slot:
        items = service.get_by_slot(current_user.id, session_id, slot)
    else:
        items = service.get_active(current_user.id, session_id)
    return WorkingMemoryList(
        memories=[WorkingMemoryResponse.model_validate(i) for i in items],
        total=len(items),
    )


@router.post("/{memory_id}/promote", response_model=dict[str, Any])
def promote_working_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Promote a working memory item to active slot."""
    service = WorkingMemoryService(db)
    success = service.promote(current_user.id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"promoted": True}


@router.post("/{memory_id}/archive", response_model=dict[str, Any])
def archive_working_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Archive a working memory item."""
    service = WorkingMemoryService(db)
    success = service.archive(current_user.id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"archived": True}


@router.post("/{memory_id}/demote", response_model=dict[str, Any])
def demote_working_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Demote a working memory item to buffer."""
    service = WorkingMemoryService(db)
    success = service.demote(current_user.id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"demoted": True}


@router.delete("/{memory_id}", status_code=204, response_model=None)
def remove_working_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a working memory item."""
    service = WorkingMemoryService(db)
    success = service.remove(current_user.id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")


@router.delete("/session/{session_id}", response_model=dict[str, Any])
def clear_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Clear all items for a session."""
    service = WorkingMemoryService(db)
    count = service.clear_session(current_user.id, session_id)
    return {"cleared": count}


@router.get("/session/{session_id}/summary", response_model=dict[str, Any])
def session_summary(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get a summary of working memory state for a session."""
    service = WorkingMemoryService(db)
    return service.get_session_summary(current_user.id, session_id)
