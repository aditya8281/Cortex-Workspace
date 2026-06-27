from __future__ import annotations

"""Tests for run persistence — RunStore, snapshots, replay buffer, PID tracking."""

import json
import os
from unittest.mock import patch

import pytest

from backend.app.agents.run_store import RunStore
from backend.app.models.cognition.agent import AgentRun, AgentStep

# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def db_session():
    """Provide an in-memory SQLite session with schema."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.app.db.base import Base

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def store(db_session):
    return RunStore(db_session)


@pytest.fixture
def sample_run(db_session):
    """Create a minimal AgentRun for testing."""
    run = AgentRun(agent_id=1, user_id=1, input_text="test input", status="running")
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


# ── PID Tracking ────────────────────────────────────────────────────────


class TestAttachPid:
    def test_attaches_current_pid(self, store, sample_run):
        store.attach_pid(sample_run.id)
        stored = store.get_pid(sample_run.id)
        assert stored == os.getpid()

    def test_attaches_specific_pid(self, store, sample_run):
        store.attach_pid(sample_run.id, pid=12345)
        assert store.get_pid(sample_run.id) == 12345

    def test_get_pid_nonexistent_run(self, store):
        assert store.get_pid(99999) is None

    def test_attach_pid_nonexistent_run(self, store):
        with pytest.raises(ValueError, match="not found"):
            store.attach_pid(99999)


# ── State Snapshots ─────────────────────────────────────────────────────


class TestStateSnapshots:
    def test_save_and_retrieve(self, store, sample_run):
        state = {"status": "completed", "output": "done", "steps": 3}
        store.save_snapshot(sample_run.id, state)
        retrieved = store.get_snapshot(sample_run.id)
        assert retrieved == state

    def test_overwrite_existing(self, store, sample_run):
        store.save_snapshot(sample_run.id, {"version": 1})
        store.save_snapshot(sample_run.id, {"version": 2})
        assert store.get_snapshot(sample_run.id) == {"version": 2}

    def test_get_snapshot_nonexistent(self, store):
        assert store.get_snapshot(99999) is None

    def test_save_nonexistent_run(self, store):
        with pytest.raises(ValueError, match="not found"):
            store.save_snapshot(99999, {})

    def test_serialises_datetime(self, store, sample_run):
        from datetime import datetime, timezone

        state = {"completed_at": datetime.now(timezone.utc)}
        store.save_snapshot(sample_run.id, state)
        retrieved = store.get_snapshot(sample_run.id)
        assert "completed_at" in retrieved
        assert isinstance(retrieved["completed_at"], str)

    def test_corrupt_snapshot_returns_none(self, store, sample_run):
        # Manually inject invalid JSON
        sample_run.state_snapshot = "{invalid"
        store.db.commit()
        assert store.get_snapshot(sample_run.id) is None


# ── Replay Buffer ───────────────────────────────────────────────────────


class TestReplayBuffer:
    def test_empty_run(self, store, sample_run):
        assert store.get_replay_buffer(sample_run.id) == []

    def test_returns_steps_oldest_first(self, store, sample_run, db_session):
        for i in range(1, 6):
            step = AgentStep(
                run_id=sample_run.id,
                step_number=i,
                action=f"step_{i}",
                action_input_json=json.dumps({"i": i}),
                observation=f"result_{i}",
                status="completed",
            )
            db_session.add(step)
        db_session.commit()

        buffer = store.get_replay_buffer(sample_run.id)
        assert len(buffer) == 5
        assert buffer[0]["step_number"] == 1
        assert buffer[-1]["step_number"] == 5

    def test_limits_to_last_n(self, store, sample_run, db_session):
        for i in range(1, 21):
            step = AgentStep(
                run_id=sample_run.id,
                step_number=i,
                action=f"step_{i}",
                status="completed",
            )
            db_session.add(step)
        db_session.commit()

        buffer = store.get_replay_buffer(sample_run.id, last_n=5)
        assert len(buffer) == 5
        assert buffer[0]["step_number"] == 16
        assert buffer[-1]["step_number"] == 20

    def test_all_steps_when_under_limit(self, store, sample_run, db_session):
        for i in range(1, 4):
            step = AgentStep(
                run_id=sample_run.id,
                step_number=i,
                action=f"step_{i}",
                status="completed",
            )
            db_session.add(step)
        db_session.commit()

        buffer = store.get_replay_buffer(sample_run.id, last_n=10)
        assert len(buffer) == 3


# ── Orphan Detection ────────────────────────────────────────────────────


class TestOrphanDetection:
    def test_no_orphans_when_no_running_runs(self, store, sample_run):
        sample_run.status = "completed"
        store.db.commit()
        orphans = store.detect_orphans()
        assert orphans == []

    def test_no_orphans_when_pid_alive(self, store, sample_run):
        sample_run.pid = os.getpid()
        store.db.commit()
        orphans = store.detect_orphans()
        assert orphans == []

    @patch.object(RunStore, "_is_pid_alive", return_value=False)
    def test_detects_dead_pid(self, mock_is_alive, store, sample_run):
        sample_run.pid = 99999
        store.db.commit()
        orphans = store.detect_orphans()
        assert len(orphans) == 1
        assert orphans[0].id == sample_run.id

    @patch.object(RunStore, "_is_pid_alive", return_value=False)
    def test_ignores_non_running(self, mock_is_alive, store, sample_run):
        sample_run.status = "completed"
        sample_run.pid = 99999
        store.db.commit()
        orphans = store.detect_orphans()
        assert orphans == []

    @patch.object(RunStore, "_is_pid_alive", return_value=False)
    def test_ignores_run_without_pid(self, mock_is_alive, store, sample_run):
        sample_run.pid = None
        store.db.commit()
        orphans = store.detect_orphans()
        assert orphans == []

    @patch.object(RunStore, "_is_pid_alive", return_value=False)
    def test_cleanup_orphan(self, mock_is_alive, store, sample_run):
        sample_run.pid = 99999
        store.db.commit()
        store.cleanup_orphan(sample_run)
        assert sample_run.status == "failed"
        assert "Orphaned" in (sample_run.error or "")

    @patch.object(RunStore, "_is_pid_alive", return_value=False)
    def test_cleanup_all_orphans(self, mock_is_alive, store, sample_run, db_session):
        sample_run.pid = 99999
        store.db.commit()

        # Create another orphan
        run2 = AgentRun(agent_id=1, user_id=1, input_text="orphan 2", status="running", pid=88888)
        db_session.add(run2)
        db_session.commit()

        cleaned = store.cleanup_all_orphans()
        assert cleaned == 2

    def test_pid_alive_true(self, store):
        assert RunStore._is_pid_alive(os.getpid()) is True

    @patch.object(RunStore, "_is_pid_alive", return_value=False)
    def test_run_with_dead_pid_cleaned(self, mock_is_alive, store, sample_run, db_session):
        """Integration: detect + cleanup in sequence."""
        sample_run.pid = 12345
        store.db.commit()

        orphans = store.detect_orphans()
        assert len(orphans) == 1

        store.cleanup_orphan(orphans[0])
        db_session.refresh(sample_run)
        assert sample_run.status == "failed"


# ── Replay ──────────────────────────────────────────────────────────────


class TestSafeJsonLoad:
    def test_valid_json(self):
        assert RunStore._safe_json_load('{"a": 1}') == {"a": 1}

    def test_invalid_json(self):
        assert RunStore._safe_json_load("{bad}") == "{bad}"

    def test_none(self):
        assert RunStore._safe_json_load(None) is None

    def test_empty_string(self):
        assert RunStore._safe_json_load("") is None
