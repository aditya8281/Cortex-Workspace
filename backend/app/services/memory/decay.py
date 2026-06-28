"""Forgetting service — Ebbinghaus-style decay for memory management."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.memory.episodic import EpisodicMemory
from backend.app.models.memory.memory_graph import MemoryEdge, MemoryNode
from backend.app.models.memory.semantic import SemanticMemory

# Decay rates per day
EPISODIC_DECAY_RATE = 0.01
SEMANTIC_DECAY_RATE = 0.005

# Confidence floor (memories never decay below this)
CONFIDENCE_FLOOR = 0.05

# Garbage collection threshold
GC_THRESHOLD = 0.1


class ForgettingService:
    """Intelligent forgetting via Ebbinghaus-style decay."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def apply_decay(self, user_id: int) -> dict:
        """Apply forgetting decay to all memories for a user."""
        episodic_decayed = self._decay_episodic(user_id)
        semantic_decayed = self._decay_semantic(user_id)

        episodic_gc = self._garbage_collect_episodic(user_id)
        semantic_gc = self._garbage_collect_semantic(user_id)

        return {
            "episodic_decayed": episodic_decayed,
            "semantic_decayed": semantic_decayed,
            "episodic_gc": episodic_gc,
            "semantic_gc": semantic_gc,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        }

    def _decay_episodic(self, user_id: int) -> int:
        """Apply decay to episodic memories. Returns count decayed."""
        memories = self.db.query(EpisodicMemory).filter(EpisodicMemory.user_id == user_id).all()

        count = 0
        for memory in memories:
            days_since_access = self._days_since(memory.last_accessed or memory.created_at)

            effective_rate = EPISODIC_DECAY_RATE / max(1.0, memory.access_count * 0.1)
            decay_factor = max(CONFIDENCE_FLOOR, 1.0 - (days_since_access * effective_rate))

            importance_damping = 0.5 + (memory.importance * 0.5)
            decay_factor = max(CONFIDENCE_FLOOR, decay_factor * importance_damping)

            new_confidence = memory.confidence * decay_factor
            if new_confidence != memory.confidence:
                memory.confidence = max(CONFIDENCE_FLOOR, new_confidence)
                count += 1

        if count > 0:
            self.db.commit()
        return count

    def _decay_semantic(self, user_id: int) -> int:
        """Apply decay to semantic memories (slower rate)."""
        memories = self.db.query(SemanticMemory).filter(SemanticMemory.user_id == user_id).all()

        count = 0
        for memory in memories:
            days_since_access = self._days_since(memory.last_accessed or memory.created_at)

            effective_rate = SEMANTIC_DECAY_RATE / max(1.0, memory.access_count * 0.1)
            decay_factor = max(CONFIDENCE_FLOOR, 1.0 - (days_since_access * effective_rate))

            new_confidence = memory.confidence * decay_factor
            if new_confidence != memory.confidence:
                memory.confidence = max(CONFIDENCE_FLOOR, new_confidence)
                count += 1

        if count > 0:
            self.db.commit()
        return count

    def _garbage_collect_episodic(self, user_id: int) -> int:
        """Remove episodic memories below confidence threshold."""
        memories = (
            self.db.query(EpisodicMemory)
            .filter(
                EpisodicMemory.user_id == user_id,
                EpisodicMemory.confidence < GC_THRESHOLD,
            )
            .all()
        )

        count = len(memories)
        for memory in memories:
            nodes = (
                self.db.query(MemoryNode)
                .filter(
                    MemoryNode.user_id == user_id,
                    MemoryNode.memory_type == "episodic",
                    MemoryNode.memory_id == memory.id,
                )
                .all()
            )
            for node in nodes:
                self.db.query(MemoryEdge).filter(
                    (MemoryEdge.source_id == node.id) | (MemoryEdge.target_id == node.id)
                ).delete(synchronize_session="fetch")
                self.db.delete(node)

            self.db.delete(memory)

        if count > 0:
            self.db.commit()
        return count

    def _garbage_collect_semantic(self, user_id: int) -> int:
        """Remove semantic memories below confidence threshold."""
        memories = (
            self.db.query(SemanticMemory)
            .filter(
                SemanticMemory.user_id == user_id,
                SemanticMemory.confidence < GC_THRESHOLD,
            )
            .all()
        )

        count = len(memories)
        for memory in memories:
            nodes = (
                self.db.query(MemoryNode)
                .filter(
                    MemoryNode.user_id == user_id,
                    MemoryNode.memory_type == "semantic",
                    MemoryNode.memory_id == memory.id,
                )
                .all()
            )
            for node in nodes:
                self.db.query(MemoryEdge).filter(
                    (MemoryEdge.source_id == node.id) | (MemoryEdge.target_id == node.id)
                ).delete(synchronize_session="fetch")
                self.db.delete(node)

            self.db.delete(memory)

        if count > 0:
            self.db.commit()
        return count

    def get_forgetting_stats(self, user_id: int) -> dict:
        """Get statistics about memory decay state."""
        episodic_count = self.db.query(EpisodicMemory).filter(EpisodicMemory.user_id == user_id).count()
        semantic_count = self.db.query(SemanticMemory).filter(SemanticMemory.user_id == user_id).count()
        episodic_low = (
            self.db.query(EpisodicMemory)
            .filter(
                EpisodicMemory.user_id == user_id,
                EpisodicMemory.confidence < GC_THRESHOLD,
            )
            .count()
        )
        semantic_low = (
            self.db.query(SemanticMemory)
            .filter(
                SemanticMemory.user_id == user_id,
                SemanticMemory.confidence < GC_THRESHOLD,
            )
            .count()
        )

        avg_ep_confidence = (
            self.db.query(func.avg(EpisodicMemory.confidence)).filter(EpisodicMemory.user_id == user_id).scalar() or 0.0
        )
        avg_sem_confidence = (
            self.db.query(func.avg(SemanticMemory.confidence)).filter(SemanticMemory.user_id == user_id).scalar() or 0.0
        )

        return {
            "total_episodic": episodic_count,
            "total_semantic": semantic_count,
            "episodic_low_confidence": episodic_low,
            "semantic_low_confidence": semantic_low,
            "avg_episodic_confidence": round(float(avg_ep_confidence), 3),
            "avg_semantic_confidence": round(float(avg_sem_confidence), 3),
            "gc_candidates": episodic_low + semantic_low,
        }

    def _days_since(self, dt: datetime) -> float:
        """Calculate days since a datetime."""
        if dt is None:
            return 0.0
        delta = datetime.now(timezone.utc).replace(tzinfo=None) - dt
        return max(0.0, delta.total_seconds() / 86400.0)
