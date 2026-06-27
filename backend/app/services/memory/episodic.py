"""Episodic memory service — CRUD, access tracking, search."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.models.memory.episodic import EpisodicMemory
from backend.app.schemas.memory.episodic import EpisodicMemoryCreate, EpisodicMemoryUpdate


class EpisodicMemoryService:
    """Service for managing episodic memories (experiences, events, conversations)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: int, data: EpisodicMemoryCreate) -> EpisodicMemory:
        """Store a new episodic memory."""
        memory = EpisodicMemory(
            user_id=user_id,
            content=data.content,
            context=data.context,
            emotion=data.emotion,
            importance=data.importance,
            confidence=0.5,
            recency_score=1.0,
            access_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def retrieve(self, user_id: int, memory_id: int) -> EpisodicMemory | None:
        """Retrieve a specific episodic memory. Increments access_count."""
        memory = (
            self.db.query(EpisodicMemory)
            .filter(
                EpisodicMemory.id == memory_id,
                EpisodicMemory.user_id == user_id,
            )
            .first()
        )
        if memory:
            memory.access_count += 1
            memory.last_accessed = datetime.utcnow()
            self.db.commit()
        return memory

    def list_recent(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> tuple[list[EpisodicMemory], int]:
        """List recent episodic memories with pagination."""
        query = self.db.query(EpisodicMemory).filter(
            EpisodicMemory.user_id == user_id
        )
        total = query.count()
        memories = (
            query.order_by(desc(EpisodicMemory.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
        return memories, total

    def list_by_importance(
        self, user_id: int, min_importance: float = 0.5, limit: int = 10
    ) -> list[EpisodicMemory]:
        """List episodic memories above an importance threshold."""
        return (
            self.db.query(EpisodicMemory)
            .filter(
                EpisodicMemory.user_id == user_id,
                EpisodicMemory.importance >= min_importance,
            )
            .order_by(desc(EpisodicMemory.importance))
            .limit(limit)
            .all()
        )

    def update(
        self, user_id: int, memory_id: int, data: EpisodicMemoryUpdate
    ) -> EpisodicMemory | None:
        """Update an episodic memory with partial data."""
        memory = (
            self.db.query(EpisodicMemory)
            .filter(
                EpisodicMemory.id == memory_id,
                EpisodicMemory.user_id == user_id,
            )
            .first()
        )
        if not memory:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(memory, key, value)
        memory.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def delete(self, user_id: int, memory_id: int) -> bool:
        """Delete an episodic memory. Cleans up graph references."""
        memory = (
            self.db.query(EpisodicMemory)
            .filter(
                EpisodicMemory.id == memory_id,
                EpisodicMemory.user_id == user_id,
            )
            .first()
        )
        if not memory:
            return False

        # Clean up graph references
        from backend.app.models.memory.memory_graph import MemoryEdge, MemoryNode

        nodes = (
            self.db.query(MemoryNode)
            .filter(
                MemoryNode.user_id == user_id,
                MemoryNode.memory_type == "episodic",
                MemoryNode.memory_id == memory_id,
            )
            .all()
        )
        for node in nodes:
            self.db.query(MemoryEdge).filter(
                (MemoryEdge.source_id == node.id) | (MemoryEdge.target_id == node.id)
            ).delete(synchronize_session="fetch")
            self.db.delete(node)

        self.db.delete(memory)
        self.db.commit()
        return True

    def search_content(
        self, user_id: int, query: str, limit: int = 10
    ) -> list[EpisodicMemory]:
        """Fulltext search across episodic memory content (ILIKE)."""
        return (
            self.db.query(EpisodicMemory)
            .filter(
                EpisodicMemory.user_id == user_id,
                EpisodicMemory.content.ilike(f"%{query}%"),
            )
            .order_by(
                desc(EpisodicMemory.importance),
                desc(EpisodicMemory.created_at),
            )
            .limit(limit)
            .all()
        )
