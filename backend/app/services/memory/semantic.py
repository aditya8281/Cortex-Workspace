"""Semantic memory service — CRUD, dedup, categorization."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.app.models.memory.semantic import SemanticMemory
from backend.app.schemas.memory.semantic import SemanticMemoryCreate, SemanticMemoryUpdate


class SemanticMemoryService:
    """Service for managing semantic memories (facts, preferences, knowledge)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: int, data: SemanticMemoryCreate) -> SemanticMemory:
        """Store a new semantic memory. Deduplicates exact content matches."""
        # Dedup check
        existing = (
            self.db.query(SemanticMemory)
            .filter(
                SemanticMemory.user_id == user_id,
                SemanticMemory.content == data.content,
            )
            .first()
        )
        if existing:
            existing.confidence = min(1.0, existing.confidence + 0.1)
            existing.access_count += 1
            existing.last_accessed = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        memory = SemanticMemory(
            user_id=user_id,
            content=data.content,
            category=data.category,
            confidence=0.5,
            source=data.source,
            access_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def retrieve(self, user_id: int, memory_id: int) -> SemanticMemory | None:
        """Retrieve a specific semantic memory. Increments access_count."""
        memory = (
            self.db.query(SemanticMemory)
            .filter(
                SemanticMemory.id == memory_id,
                SemanticMemory.user_id == user_id,
            )
            .first()
        )
        if memory:
            memory.access_count += 1
            memory.last_accessed = datetime.utcnow()
            self.db.commit()
        return memory

    def list_by_category(self, user_id: int, category: str, limit: int = 50) -> list[SemanticMemory]:
        """List semantic memories by category."""
        return (
            self.db.query(SemanticMemory)
            .filter(
                SemanticMemory.user_id == user_id,
                SemanticMemory.category == category,
            )
            .order_by(desc(SemanticMemory.confidence))
            .limit(limit)
            .all()
        )

    def list_all(self, user_id: int, limit: int = 50, offset: int = 0) -> tuple[list[SemanticMemory], int]:
        """List all semantic memories with pagination."""
        query = self.db.query(SemanticMemory).filter(SemanticMemory.user_id == user_id)
        total = query.count()
        memories = query.order_by(desc(SemanticMemory.confidence)).offset(offset).limit(limit).all()
        return memories, total

    def search_content(self, user_id: int, query: str, limit: int = 10) -> list[SemanticMemory]:
        """Fulltext search across semantic memory content (ILIKE)."""
        return (
            self.db.query(SemanticMemory)
            .filter(
                SemanticMemory.user_id == user_id,
                SemanticMemory.content.ilike(f"%{query}%"),
            )
            .order_by(
                desc(SemanticMemory.confidence),
                desc(SemanticMemory.access_count),
            )
            .limit(limit)
            .all()
        )

    def update(self, user_id: int, memory_id: int, data: SemanticMemoryUpdate) -> SemanticMemory | None:
        """Update a semantic memory with partial data."""
        memory = (
            self.db.query(SemanticMemory)
            .filter(
                SemanticMemory.id == memory_id,
                SemanticMemory.user_id == user_id,
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
        """Delete a semantic memory with graph cleanup."""
        memory = (
            self.db.query(SemanticMemory)
            .filter(
                SemanticMemory.id == memory_id,
                SemanticMemory.user_id == user_id,
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
                MemoryNode.memory_type == "semantic",
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

    def get_categories(self, user_id: int) -> list[dict]:
        """Get all categories with counts for this user."""
        results = (
            self.db.query(
                SemanticMemory.category,
                func.count(SemanticMemory.id).label("count"),
            )
            .filter(SemanticMemory.user_id == user_id)
            .group_by(SemanticMemory.category)
            .all()
        )
        return [{"category": r.category, "count": r.count} for r in results]
