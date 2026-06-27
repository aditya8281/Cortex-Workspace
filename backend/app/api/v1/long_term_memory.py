from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.models.memory.long_term_memory import LongTermMemory
from backend.app.services.memory.long_term import LongTermMemoryService

router = APIRouter()


class CreateMemoryRequest(BaseModel):
    category: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=256)
    content: str = Field(min_length=1, max_length=10000)
    source: str | None = Field(default=None, max_length=512)
    source_id: int | None = None
    tags: list[str] | None = None


class LongTermMemoryItem(BaseModel):
    id: int
    category: str
    title: str
    content: str
    confidence: float
    access_count: int
    source: str | None = None
    created_at: str | None = None


class LongTermMemoryListResponse(BaseModel):
    memories: list[LongTermMemoryItem] | None = None
    grouped: dict[str, list[LongTermMemoryItem]] | None = None


class LongTermMemoryStatsResponse(BaseModel):
    total: int
    active: int
    by_category: dict[str, int]
    avg_confidence: float


class LongTermMemoryCreateResponse(BaseModel):
    id: int
    status: str


class LongTermMemoryReinforceResponse(BaseModel):
    confidence: float


class LongTermMemoryDeleteResponse(BaseModel):
    status: str


def _serialize_memory(m: LongTermMemory) -> LongTermMemoryItem:
    return LongTermMemoryItem(
        id=m.id,
        category=m.category,
        title=m.title,
        content=m.content,
        confidence=m.confidence,
        access_count=m.access_count,
        source=m.source,
        created_at=m.created_at.isoformat() if m.created_at else None,
    )


@router.get("/long-term-memory", response_model=LongTermMemoryListResponse)
def list_memories(
    category: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = LongTermMemoryService(db)
    if category:
        return LongTermMemoryListResponse(
            memories=[_serialize_memory(m) for m in service.search(user.id, category=category)]
        )
    grouped = service.list_by_category(user.id)
    return LongTermMemoryListResponse(
        grouped={cat: [_serialize_memory(m) for m in memories] for cat, memories in grouped.items()}
    )


@router.get("/long-term-memory/stats", response_model=LongTermMemoryStatsResponse)
def memory_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return LongTermMemoryService(db).get_stats(user.id)


@router.post("/long-term-memory", response_model=LongTermMemoryCreateResponse)
def create_memory(
    payload: CreateMemoryRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = LongTermMemoryService(db)
    memory = service.create(
        user.id,
        category=payload.category,
        title=payload.title,
        content=payload.content,
        source=payload.source,
        source_id=payload.source_id,
        tags=payload.tags,
    )
    return {"id": memory.id, "status": "created"}


@router.post("/long-term-memory/{memory_id}/reinforce", response_model=LongTermMemoryReinforceResponse)
def reinforce_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = LongTermMemoryService(db)
    memory = db.get(LongTermMemory, memory_id)
    if not memory or memory.user_id != user.id:
        raise HTTPException(status_code=404, detail="Memory not found")
    reinforced = service.reinforce(memory_id)
    if not reinforced:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"confidence": reinforced.confidence}


@router.delete("/long-term-memory/{memory_id}", response_model=LongTermMemoryDeleteResponse)
def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    memory = db.get(LongTermMemory, memory_id)
    if not memory or memory.user_id != user.id:
        raise HTTPException(status_code=404, detail="Memory not found")
    memory.is_active = False
    db.commit()
    return {"status": "deleted"}
