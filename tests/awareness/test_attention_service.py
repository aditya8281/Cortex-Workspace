"""Tests for AttentionService."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from backend.app.services.awareness.attention_service import AttentionService


def _naive_now() -> datetime:
    """Return a naive datetime that matches SQLite's storage format."""
    return datetime(2026, 6, 30, 12, 0, 0)


class TestAttentionService:
    def test_start_session(self, db_session: Session) -> None:
        """Starting a session creates a tracker with the provided details."""
        svc = AttentionService(db_session)
        tracker = svc.start_session(user_id=1, session_type="coding", task_description="Test task")
        assert tracker.id is not None
        assert tracker.user_id == 1
        assert tracker.session_type == "coding"
        assert tracker.task_description == "Test task"
        assert tracker.ended_at is None

    def test_start_session_default_type(self, db_session: Session) -> None:
        """Starting a session without type defaults to 'general'."""
        svc = AttentionService(db_session)
        tracker = svc.start_session(user_id=1)
        assert tracker.session_type == "general"

    def test_start_session_no_task(self, db_session: Session) -> None:
        """Starting a session without a task description leaves it None."""
        svc = AttentionService(db_session)
        tracker = svc.start_session(user_id=1)
        assert tracker.task_description is None

    def test_start_multiple_sessions(self, db_session: Session) -> None:
        """Starting multiple sessions creates separate records."""
        svc = AttentionService(db_session)
        t1 = svc.start_session(user_id=1, session_type="coding")
        t2 = svc.start_session(user_id=1, session_type="research")
        assert t1.id != t2.id
        assert t1.session_type == "coding"
        assert t2.session_type == "research"

    def test_end_session(self, db_session: Session) -> None:
        """Ending a session sets ended_at and computes duration.

        SQLite stores started_at as naive datetime, so we mock
        datetime.now to return a naive datetime for compatible subtraction.
        """
        svc = AttentionService(db_session)
        tracker = svc.start_session(user_id=1)

        mock_dt = type("MockDT", (), {
            "now": staticmethod(lambda *a, **kw: _naive_now()),
            "timezone": type("tz", (), {"utc": None})(),
        })()
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "backend.app.services.awareness.attention_service.datetime",
                mock_dt,
            )
            ended = svc.end_session(tracker.id)
        assert ended.ended_at is not None
        assert ended.duration_seconds >= 0

    def test_end_session_not_found(self, db_session: Session) -> None:
        """Ending a non-existent session raises ValueError."""
        svc = AttentionService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.end_session(999)

    def test_end_session_already_ended(self, db_session: Session) -> None:
        """Ending an already-ended session raises ValueError."""
        svc = AttentionService(db_session)
        tracker = svc.start_session(user_id=1)

        mock_dt = type("MockDT", (), {
            "now": staticmethod(lambda *a, **kw: _naive_now()),
            "timezone": type("tz", (), {"utc": None})(),
        })()
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "backend.app.services.awareness.attention_service.datetime",
                mock_dt,
            )
            svc.end_session(tracker.id)
        with pytest.raises(ValueError, match="already ended"):
            svc.end_session(tracker.id)

    def test_update_focus(self, db_session: Session) -> None:
        """Updating focus sets the score and distraction count."""
        svc = AttentionService(db_session)
        tracker = svc.start_session(user_id=1)
        updated = svc.update_focus(tracker.id, focus_score=85.5, distraction_count=2)
        assert updated.focus_score == 85.5
        assert updated.distraction_count == 2

    def test_update_focus_switch_count(self, db_session: Session) -> None:
        """Updating focus can also set the switch count."""
        svc = AttentionService(db_session)
        tracker = svc.start_session(user_id=1)
        updated = svc.update_focus(tracker.id, focus_score=50.0, switch_count=3)
        assert updated.switch_count == 3

    def test_update_focus_clamps_high(self, db_session: Session) -> None:
        """Focus score is clamped to max 100."""
        svc = AttentionService(db_session)
        tracker = svc.start_session(user_id=1)
        updated = svc.update_focus(tracker.id, focus_score=150.0)
        assert updated.focus_score == 100.0

    def test_update_focus_clamps_low(self, db_session: Session) -> None:
        """Focus score is clamped to min 0."""
        svc = AttentionService(db_session)
        tracker = svc.start_session(user_id=1)
        updated = svc.update_focus(tracker.id, focus_score=-10.0)
        assert updated.focus_score == 0.0

    def test_update_focus_not_found(self, db_session: Session) -> None:
        """Updating focus on a non-existent session raises ValueError."""
        svc = AttentionService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.update_focus(999, 50.0)

    def test_get_stats_empty(self, db_session: Session) -> None:
        """Stats with no sessions returns zero counts."""
        svc = AttentionService(db_session)
        stats = svc.get_stats(user_id=1)
        assert stats["total_sessions"] == 0
        assert stats["avg_focus_score"] == 0
        assert stats["avg_duration"] == 0
        assert stats["total_productive_time"] == 0
        assert stats["sessions_by_type"] == {}

    def test_get_stats_with_sessions(self, db_session: Session) -> None:
        """Stats aggregate sessions by type correctly."""
        svc = AttentionService(db_session)
        svc.start_session(user_id=1, session_type="coding")
        svc.start_session(user_id=1, session_type="coding")
        svc.start_session(user_id=1, session_type="research")
        stats = svc.get_stats(user_id=1)
        assert stats["total_sessions"] == 3
        assert stats["sessions_by_type"]["coding"] == 2
        assert stats["sessions_by_type"]["research"] == 1

    def test_get_stats_user_isolation(self, db_session: Session) -> None:
        """Stats are isolated by user_id."""
        svc = AttentionService(db_session)
        svc.start_session(user_id=1, session_type="coding")
        svc.start_session(user_id=2, session_type="research")
        stats_u1 = svc.get_stats(user_id=1)
        stats_u2 = svc.get_stats(user_id=2)
        assert stats_u1["total_sessions"] == 1
        assert stats_u2["total_sessions"] == 1

    def test_get_sessions(self, db_session: Session) -> None:
        """Getting sessions returns all sessions for the user."""
        svc = AttentionService(db_session)
        svc.start_session(user_id=1)
        svc.start_session(user_id=1)
        sessions = svc.get_sessions(user_id=1)
        assert len(sessions) == 2

    def test_get_sessions_empty(self, db_session: Session) -> None:
        """Getting sessions with no data returns empty list."""
        svc = AttentionService(db_session)
        sessions = svc.get_sessions(user_id=1)
        assert sessions == []

    def test_get_sessions_respects_limit(self, db_session: Session) -> None:
        """Getting sessions respects the limit parameter."""
        svc = AttentionService(db_session)
        for _ in range(5):
            svc.start_session(user_id=1)
        sessions = svc.get_sessions(user_id=1, limit=3)
        assert len(sessions) == 3

    def test_get_sessions_user_isolation(self, db_session: Session) -> None:
        """Getting sessions is isolated by user_id."""
        svc = AttentionService(db_session)
        svc.start_session(user_id=1)
        svc.start_session(user_id=2)
        assert len(svc.get_sessions(user_id=1)) == 1
        assert len(svc.get_sessions(user_id=2)) == 1
