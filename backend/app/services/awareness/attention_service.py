"""Attention tracker — manages focus sessions, scores, and productivity stats."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.awareness.attention_tracker import AttentionTracker

logger = logging.getLogger(__name__)


def _utcnow_naive() -> datetime:
    """Return a naive UTC datetime for SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AttentionService:
    """Manages focus/attention tracking sessions and productivity stats."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def start_session(
        self,
        user_id: int,
        session_type: str = "general",
        task_description: str | None = None,
    ) -> AttentionTracker:
        """Start a new attention tracking session."""
        tracker = AttentionTracker(
            user_id=user_id,
            session_type=session_type,
            task_description=task_description,
        )
        self.db.add(tracker)
        self.db.commit()
        self.db.refresh(tracker)
        logger.info("Started attention session %d (type=%s)", tracker.id, session_type)
        return tracker

    def end_session(self, session_id: int) -> AttentionTracker:
        """End an active attention session and compute duration."""
        tracker = self.db.query(AttentionTracker).filter(AttentionTracker.id == session_id).first()
        if not tracker:
            raise ValueError(f"Session {session_id} not found")
        if tracker.ended_at:
            raise ValueError(f"Session {session_id} already ended")

        tracker.ended_at = _utcnow_naive()
        if tracker.started_at:
            delta = (tracker.ended_at - tracker.started_at).total_seconds()
            tracker.duration_seconds = max(0.0, delta)
            tracker.productive_seconds = delta * (tracker.focus_score / 100.0) if tracker.focus_score else 0

        self.db.commit()
        self.db.refresh(tracker)
        logger.info("Ended attention session %d (duration=%.0fs)", session_id, tracker.duration_seconds or 0)
        return tracker

    def update_focus(
        self,
        session_id: int,
        focus_score: float,
        distraction_count: int | None = None,
        switch_count: int | None = None,
    ) -> AttentionTracker:
        """Update focus metrics for an active session."""
        tracker = self.db.query(AttentionTracker).filter(AttentionTracker.id == session_id).first()
        if not tracker:
            raise ValueError(f"Session {session_id} not found")

        tracker.focus_score = max(0.0, min(100.0, focus_score))
        if distraction_count is not None:
            tracker.distraction_count = distraction_count
        if switch_count is not None:
            tracker.switch_count = switch_count

        self.db.commit()
        self.db.refresh(tracker)
        return tracker

    def get_stats(self, user_id: int) -> dict:
        """Get aggregated attention stats for a user."""
        sessions = self.db.query(AttentionTracker).filter(AttentionTracker.user_id == user_id).all()
        if not sessions:
            return {
                "total_sessions": 0,
                "avg_focus_score": 0,
                "avg_duration": 0,
                "total_productive_time": 0,
                "sessions_by_type": {},
            }

        by_type: dict[str, int] = {}
        for s in sessions:
            by_type[s.session_type] = by_type.get(s.session_type, 0) + 1

        return {
            "total_sessions": len(sessions),
            "avg_focus_score": sum(s.focus_score for s in sessions) / len(sessions),
            "avg_duration": sum(s.duration_seconds for s in sessions) / len(sessions),
            "total_productive_time": sum(s.productive_seconds for s in sessions),
            "sessions_by_type": by_type,
        }

    def get_sessions(self, user_id: int, limit: int = 50) -> list[AttentionTracker]:
        """Get recent attention sessions for a user."""
        return (
            self.db.query(AttentionTracker)
            .filter(AttentionTracker.user_id == user_id)
            .order_by(AttentionTracker.created_at.desc())
            .limit(limit)
            .all()
        )
