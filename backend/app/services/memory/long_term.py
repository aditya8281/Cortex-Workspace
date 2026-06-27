from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.memory.long_term_memory import LongTermMemory

CATEGORIES = ("preference", "pattern", "correction", "fact", "context")


class LongTermMemoryService:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        category: str,
        title: str,
        content: str,
        source: str | None = None,
        source_id: int | None = None,
        tags: list | None = None,
    ) -> LongTermMemory:
        if category not in CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of {CATEGORIES}")
        memory = LongTermMemory(
            user_id=user_id,
            category=category,
            title=title,
            content=content,
            source=source,
            source_id=source_id,
            tags=tags or [],
            confidence=0.5,
            access_count=0,
        )
        self.db.add(memory)
        self.db.commit()
        return memory

    def reinforce(self, memory_id: int, amount: float = 0.1) -> LongTermMemory | None:
        memory = self.db.get(LongTermMemory, memory_id)
        if memory:
            memory.confidence = min(1.0, memory.confidence + amount)
            memory.access_count += 1
            memory.last_accessed_at = func.now()
            self.db.commit()
        return memory

    def decay(self, user_id: int) -> int:
        """Apply time-based decay to all active memories for a user. Returns count of decayed memories."""
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import and_, update

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=30)

        stmt = (
            update(LongTermMemory)
            .where(
                and_(
                    LongTermMemory.user_id == user_id,
                    LongTermMemory.is_active == True,  # noqa: E712
                    LongTermMemory.last_accessed_at < cutoff,
                )
            )
            .values(
                confidence=LongTermMemory.confidence * 0.95,
                decayed_at=now,
            )
        )
        result = self.db.execute(stmt)  # type: ignore[assignment]
        self.db.commit()
        return result.rowcount  # type: ignore[attr-defined]

    def search(
        self,
        user_id: int,
        query: str | None = None,
        category: str | None = None,
        min_confidence: float = 0.1,
        limit: int = 20,
    ) -> list[LongTermMemory]:
        q = self.db.query(LongTermMemory).filter(
            LongTermMemory.user_id == user_id,
            LongTermMemory.is_active == True,  # noqa: E712
            LongTermMemory.confidence >= min_confidence,
        )
        if category:
            q = q.filter(LongTermMemory.category == category)
        if query:
            q = q.filter(LongTermMemory.title.ilike(f"%{query}%") | LongTermMemory.content.ilike(f"%{query}%"))
        return q.order_by(LongTermMemory.confidence.desc()).limit(limit).all()

    def list_by_category(self, user_id: int) -> dict[str, list[LongTermMemory]]:
        memories = self.search(user_id, min_confidence=0.0)
        grouped: dict[str, list[LongTermMemory]] = {cat: [] for cat in CATEGORIES}
        for m in memories:
            if m.category in grouped:
                grouped[m.category].append(m)
        return grouped

    def get_stats(self, user_id: int) -> dict:
        memories = self.db.query(LongTermMemory).filter(LongTermMemory.user_id == user_id).all()
        active = [m for m in memories if m.is_active]
        return {
            "total": len(memories),
            "active": len(active),
            "by_category": {cat: len([m for m in active if m.category == cat]) for cat in CATEGORIES},
            "avg_confidence": sum(m.confidence for m in active) / len(active) if active else 0,
        }
