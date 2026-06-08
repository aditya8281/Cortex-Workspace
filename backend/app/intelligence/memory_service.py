"""Persistent knowledge memory — search and store discovered intelligence.

Uses keyword-based search over KnowledgeEntry records. No embedding or
vector dependencies required.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.intelligence.models import KnowledgeEntry


class PersistentMemoryService:
    """Search and store knowledge entries using keyword matching."""

    def search(self, db: Session, query: str, limit: int = 8, user_id: int | None = None) -> list[dict]:
        words = [w.lower() for w in query.split() if len(w) > 2]
        if not words:
            return []

        q = db.query(KnowledgeEntry)
        if user_id is not None:
            q = q.filter(
                (KnowledgeEntry.user_id == user_id) | (KnowledgeEntry.user_id.is_(None))
            )

        entries = q.order_by(KnowledgeEntry.updated_at.desc()).limit(200).all()
        if not entries:
            return []

        scored: list[tuple[float, KnowledgeEntry]] = []
        for entry in entries:
            haystack = f"{entry.title} {entry.content} {entry.category}".lower()
            keyword_score = sum(1 for w in words if w in haystack)
            recency_boost = 0.0
            if entry.updated_at is not None:
                age_days = max(0.0, (datetime.utcnow() - entry.updated_at).total_seconds() / 86400.0)
                recency_boost = max(0.0, 0.08 - min(age_days, 30.0) * 0.002)
            score = (min(keyword_score, 5) * 0.18) + recency_boost
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "id": entry.id,
                "category": entry.category,
                "title": entry.title,
                "content": entry.content[:1200],
                "source_path": entry.source_path,
                "score": round(score, 4),
            }
            for score, entry in scored[:limit]
        ]

    def add_document_memory(
        self,
        db: Session,
        *,
        title: str,
        content: str,
        source_path: str,
        category: str = "document",
        user_id: int | None = None,
    ) -> KnowledgeEntry:
        source_key = f"doc:{source_path}"
        existing = (
            db.query(KnowledgeEntry).filter(KnowledgeEntry.source_key == source_key).first()
        )
        if existing is None:
            existing = KnowledgeEntry(
                category=category,
                title=title,
                content=content,
                source_path=source_path,
                source_key=source_key,
                user_id=user_id,
            )
            db.add(existing)
        else:
            existing.title = title
            existing.content = content
            existing.category = category
            existing.source_path = source_path
            existing.user_id = user_id

        db.flush()
        return existing

    def count_entries(self, db: Session, user_id: int | None = None) -> int:
        q = db.query(KnowledgeEntry)
        if user_id is not None:
            q = q.filter(
                (KnowledgeEntry.user_id == user_id) | (KnowledgeEntry.user_id.is_(None))
            )
        return q.count()
