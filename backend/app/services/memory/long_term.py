from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.memory.long_term_memory import LongTermMemory

if TYPE_CHECKING:
    from backend.app.services.storage.user_workspace import UserWorkspace

logger = logging.getLogger(__name__)

CATEGORIES = ("preference", "pattern", "correction", "fact", "context", "personality")


class LongTermMemoryService:
    """Dual-write memory service — DB + filesystem simultaneously.

    When a workspace is provided, all writes go to both DB and filesystem.
    Filesystem is the durable backup; DB enables SQL search/query.
    """

    def __init__(self, db: Session, workspace: UserWorkspace | None = None):
        self.db = db
        self._ws = workspace

    # ── Helpers ───────────────────────────────────────────────────────

    def _filesystem_id(self, db_id: int) -> int:
        """MemoryStore uses its own numeric IDs. Negate the DB id to avoid
        collision — the sign tells us this entry originated from Postgres."""
        return -(db_id + 1)

    def _store_ids_from_db(self, db_memory: LongTermMemory) -> dict:
        """Build fields for MemoryStore, keyed by the fs ID."""
        return {
            "id": self._filesystem_id(db_memory.id),
            "category": db_memory.category,
            "title": db_memory.title,
            "content": db_memory.content,
            "confidence": db_memory.confidence,
            "source": db_memory.source or "",
            "source_id": db_memory.source_id,
            "access_count": db_memory.access_count,
            "created_at": db_memory.created_at.timestamp() if db_memory.created_at else time.time(),
        }

    # ── CRUD ──────────────────────────────────────────────────────────

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
        self.db.refresh(memory)

        # Dual-write to filesystem
        if self._ws:
            try:
                entry = self._store_ids_from_db(memory)
                memories = self._ws.memory.load_memories()
                # Check for duplicate by title + content hash
                content_hash = hash((title, content))
                dupes = [m for m in memories if hash((m.get("title", ""), m.get("content", ""))) == content_hash]
                if dupes:
                    existing = dupes[0]
                    existing.update(entry)
                    logger.debug("Updated duplicate memory '%s' in filesystem", title)
                else:
                    memories.append(entry)
                self._ws.memory.save_memories(memories)
            except Exception as exc:
                logger.warning("Filesystem memory write failed for '%s': %s", title, exc)

        return memory

    def reinforce(self, memory_id: int, amount: float = 0.1) -> LongTermMemory | None:
        memory = self.db.get(LongTermMemory, memory_id)
        if memory:
            memory.confidence = min(1.0, memory.confidence + amount)
            memory.access_count += 1
            memory.last_accessed_at = func.now()
            self.db.commit()

            # Dual-write: reinforce in filesystem too
            if self._ws:
                try:
                    fs_id = self._filesystem_id(memory_id)
                    self._ws.memory.reinforce_memory(fs_id, amount)
                except Exception as exc:
                    logger.debug("Filesystem memory reinforce failed: %s", exc)

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
        results = q.order_by(LongTermMemory.confidence.desc()).limit(limit).all()

        # Filesystem fallback: if Postgres returned nothing, try filesystem
        if not results and self._ws:
            try:
                fs_memories = self._ws.memory.search_memories(
                    query=query or "",
                    min_confidence=min_confidence,
                    limit=limit,
                )
                # Convert filesystem dicts to LongTermMemory objects
                for m in fs_memories:
                    ltm = LongTermMemory(
                        id=abs(m.get("id", 0)) - 1 if m.get("id", 0) < 0 else m.get("id", 0),
                        user_id=user_id,
                        category=m.get("category", "fact"),
                        title=m.get("title", ""),
                        content=m.get("content", ""),
                        confidence=m.get("confidence", 0.5),
                        source=m.get("source", ""),
                        source_id=m.get("source_id"),
                        tags=[],
                        access_count=m.get("access_count", 0),
                        is_active=True,
                    )
                    results.append(ltm)
            except Exception as exc:
                logger.debug("Filesystem memory search failed: %s", exc)

        return results

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
