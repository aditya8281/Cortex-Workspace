"""Working memory service — session-scoped context with slot management."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.models.memory.working import WorkingMemory

# Default working memory TTL: 1 hour
DEFAULT_TTL_HOURS = 1
# Maximum active items per session
MAX_ACTIVE_ITEMS = 20
# Maximum buffer items per session
MAX_BUFFER_ITEMS = 10


class WorkingMemoryService:
    """Service for managing session-scoped working memory.

    Working memory is a volatile, session-scoped context buffer.
    Items auto-expire after configurable TTL (default: 1 hour).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(
        self,
        user_id: int,
        session_id: str,
        content: str,
        slot: str = "active",
        priority: int = 0,
        ttl_hours: float = DEFAULT_TTL_HOURS,
    ) -> WorkingMemory:
        """Add an item to working memory."""
        memory = WorkingMemory(
            user_id=user_id,
            session_id=session_id,
            content=content,
            slot=slot,
            priority=priority,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def get_active(self, user_id: int, session_id: str) -> list[WorkingMemory]:
        """Get active items in working memory, ordered by priority."""
        return (
            self.db.query(WorkingMemory)
            .filter(
                WorkingMemory.user_id == user_id,
                WorkingMemory.session_id == session_id,
                WorkingMemory.slot == "active",
                WorkingMemory.expires_at > datetime.utcnow(),
            )
            .order_by(desc(WorkingMemory.priority))
            .all()
        )

    def get_by_slot(self, user_id: int, session_id: str, slot: str) -> list[WorkingMemory]:
        """Get items in a specific slot."""
        return (
            self.db.query(WorkingMemory)
            .filter(
                WorkingMemory.user_id == user_id,
                WorkingMemory.session_id == session_id,
                WorkingMemory.slot == slot,
                WorkingMemory.expires_at > datetime.utcnow(),
            )
            .order_by(desc(WorkingMemory.priority))
            .all()
        )

    def promote(self, user_id: int, memory_id: int) -> bool:
        """Promote an item to the active slot."""
        memory = (
            self.db.query(WorkingMemory)
            .filter(
                WorkingMemory.id == memory_id,
                WorkingMemory.user_id == user_id,
            )
            .first()
        )
        if not memory:
            return False

        # Check active slot capacity
        active_count = (
            self.db.query(WorkingMemory)
            .filter(
                WorkingMemory.user_id == user_id,
                WorkingMemory.session_id == memory.session_id,
                WorkingMemory.slot == "active",
            )
            .count()
        )

        if active_count >= MAX_ACTIVE_ITEMS:
            # Demote lowest-priority active item to buffer
            lowest = (
                self.db.query(WorkingMemory)
                .filter(
                    WorkingMemory.user_id == user_id,
                    WorkingMemory.session_id == memory.session_id,
                    WorkingMemory.slot == "active",
                )
                .order_by(WorkingMemory.priority)
                .first()
            )
            if lowest:
                lowest.slot = "buffer"

        memory.slot = "active"
        self.db.commit()
        return True

    def archive(self, user_id: int, memory_id: int) -> bool:
        """Archive an item from working memory."""
        memory = (
            self.db.query(WorkingMemory)
            .filter(
                WorkingMemory.id == memory_id,
                WorkingMemory.user_id == user_id,
            )
            .first()
        )
        if not memory:
            return False
        memory.slot = "archive"
        self.db.commit()
        return True

    def demote(self, user_id: int, memory_id: int) -> bool:
        """Demote an item from active to buffer."""
        memory = (
            self.db.query(WorkingMemory)
            .filter(
                WorkingMemory.id == memory_id,
                WorkingMemory.user_id == user_id,
            )
            .first()
        )
        if not memory:
            return False
        memory.slot = "buffer"
        self.db.commit()
        return True

    def remove(self, user_id: int, memory_id: int) -> bool:
        """Remove an item from working memory entirely."""
        memory = (
            self.db.query(WorkingMemory)
            .filter(
                WorkingMemory.id == memory_id,
                WorkingMemory.user_id == user_id,
            )
            .first()
        )
        if not memory:
            return False
        self.db.delete(memory)
        self.db.commit()
        return True

    def cleanup_expired(self, user_id: int, session_id: str) -> int:
        """Remove expired items from working memory.

        Returns:
            Number of items removed.
        """
        expired = (
            self.db.query(WorkingMemory)
            .filter(
                WorkingMemory.user_id == user_id,
                WorkingMemory.session_id == session_id,
                WorkingMemory.expires_at < datetime.utcnow(),
            )
            .all()
        )

        count = len(expired)
        for memory in expired:
            self.db.delete(memory)

        if count > 0:
            self.db.commit()
        return count

    def clear_session(self, user_id: int, session_id: str) -> int:
        """Clear all items for a session. Used on session end."""
        items = (
            self.db.query(WorkingMemory)
            .filter(
                WorkingMemory.user_id == user_id,
                WorkingMemory.session_id == session_id,
            )
            .all()
        )

        count = len(items)
        for item in items:
            self.db.delete(item)

        if count > 0:
            self.db.commit()
        return count

    def get_session_summary(self, user_id: int, session_id: str) -> dict:
        """Get a summary of working memory state for a session."""
        items = (
            self.db.query(WorkingMemory)
            .filter(
                WorkingMemory.user_id == user_id,
                WorkingMemory.session_id == session_id,
            )
            .all()
        )

        return {
            "total_items": len(items),
            "active": len([i for i in items if i.slot == "active"]),
            "buffer": len([i for i in items if i.slot == "buffer"]),
            "archive": len([i for i in items if i.slot == "archive"]),
            "expired": len([i for i in items if i.expires_at < datetime.utcnow()]),
        }
