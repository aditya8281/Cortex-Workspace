from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_optional, get_db
from backend.app.intelligence.models import KnowledgeEntry
from backend.app.models.user import User

router = APIRouter()


class MemoryCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1)
    category: str = Field(default="note", min_length=1, max_length=64)
    source_path: str | None = Field(default=None, max_length=1024)


def _serialize_memory(entry: KnowledgeEntry) -> dict[str, object]:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "category": entry.category,
        "title": entry.title,
        "content": entry.content,
        "source_path": entry.source_path,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }


@router.get("/api/memory")
def read_memory(
    limit: int = 24,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)
    query = db.query(KnowledgeEntry)
    category_query = db.query(KnowledgeEntry)
    if current_user is not None:
        filter_clause = (KnowledgeEntry.user_id == current_user.id) | (KnowledgeEntry.user_id.is_(None))
        query = query.filter(filter_clause)
        category_query = category_query.filter(filter_clause)

    total = query.count()
    entries = query.order_by(KnowledgeEntry.updated_at.desc()).offset(safe_offset).limit(safe_limit).all()
    categories = category_query.group_by(KnowledgeEntry.category).with_entities(
        KnowledgeEntry.category,
        func.count(KnowledgeEntry.id),
    ).all()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "count": len(entries),
        "offset": safe_offset,
        "limit": safe_limit,
        "categories": {category: count for category, count in categories},
        "entries": [_serialize_memory(entry) for entry in entries],
    }


@router.post("/api/memory")
def write_memory(
    payload: MemoryCreatePayload,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    entry = KnowledgeEntry(
        user_id=current_user.id if current_user else None,
        category=payload.category,
        title=payload.title,
        content=payload.content,
        source_path=payload.source_path,
        source_key=f"manual:{payload.category}:{payload.title}:{datetime.now(timezone.utc).timestamp()}",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {
        "status": "stored",
        "entry": _serialize_memory(entry),
    }
