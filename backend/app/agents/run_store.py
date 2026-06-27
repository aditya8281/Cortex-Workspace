"""Run persistence — state snapshots, replay buffer, PID tracking, orphan detection.

Extends the basic AgentRun/AgentStep storage in run_manager.py with:
- **State snapshots:** JSON-serialised run state saved after each step for
  crash recovery (resume from last snapshot).
- **Replay buffer:** Retrieve the last N steps of a run for context rebuilding.
- **PID tracking:** Attach the OS PID to a run so long-running tasks can be
  monitored and orphaned runs detected.
- **Orphan detection:** Find runs whose PID is no longer alive and clean them
  up automatically.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.cognition.agent import AgentRun

logger = logging.getLogger(__name__)

# Default number of recent steps to return in replay buffer
_DEFAULT_REPLAY_N = 10

# Grace period before a run is considered orphaned (seconds)
_DEFAULT_ORPHAN_AGE_S = 300


class RunStore:
    """Persistence layer for agent runs — snapshots, replay, PID tracking.

    Parameters
    ----------
    db:
        An active SQLAlchemy session.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── PID tracking ────────────────────────────────────────────────────

    def attach_pid(self, run_id: int, pid: int | None = None) -> None:
        """Record the current process PID for *run_id*.

        If *pid* is ``None`` the current OS PID is used.
        """
        pid = pid or os.getpid()
        run = self.db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if run is None:
            raise ValueError(f"Run {run_id} not found")
        run.pid = pid
        self.db.commit()

    def get_pid(self, run_id: int) -> int | None:
        """Return the PID attached to *run_id*, or ``None``."""
        run = self.db.query(AgentRun).filter(AgentRun.id == run_id).first()
        return run.pid if run else None

    # ── Orphan detection ────────────────────────────────────────────────

    @staticmethod
    def _is_pid_alive(pid: int) -> bool:
        """Check if a process with *pid* is still running.

        Uses ``os.kill(pid, 0)`` which is the Posix-standard way to test
        for process existence without actually sending a signal.
        """
        try:
            os.kill(pid, 0)
            return True
        except PermissionError:
            # Process exists but we can't signal it — treat as alive
            return True
        except ProcessLookupError:
            return False

    def detect_orphans(
        self,
        max_age_seconds: int = _DEFAULT_ORPHAN_AGE_S,
    ) -> list[AgentRun]:
        """Find runs that are marked ``running`` but whose PID is dead.

        Parameters
        ----------
        max_age_seconds:
            Only consider runs created at least this many seconds ago
            (avoids flagging runs that haven't attached a PID yet).

        Returns
        -------
        list[AgentRun]
            Runs determined to be orphaned.
        """
        cutoff = datetime.now(timezone.utc)
        orphans: list[AgentRun] = []
        # We iterate because the number of active runs is typically small (< 100).
        # A single query would be more efficient but less portable across DB backends.
        active_runs = (
            self.db.query(AgentRun)
            .filter(
                AgentRun.status == "running",
                AgentRun.pid.isnot(None),
                AgentRun.created_at < cutoff,  # noqa: SIM115
            )
            .all()
        )

        for run in active_runs:
            if run.pid is not None and not self._is_pid_alive(run.pid):
                orphans.append(run)

        return orphans

    def cleanup_orphan(self, run: AgentRun) -> None:
        """Mark *run* as failed and set orphan error message."""
        run.status = "failed"
        run.error = "Orphaned run — process no longer alive"
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()

    def cleanup_all_orphans(
        self,
        max_age_seconds: int = _DEFAULT_ORPHAN_AGE_S,
    ) -> int:
        """Detect and clean up all orphans. Returns the number cleaned."""
        orphans = self.detect_orphans(max_age_seconds=max_age_seconds)
        for run in orphans:
            self.cleanup_orphan(run)
            logger.info("Cleaned up orphaned run %d (pid=%d)", run.id, run.pid)
        return len(orphans)

    # ── State snapshots ─────────────────────────────────────────────────

    def save_snapshot(self, run_id: int, state: dict[str, Any]) -> None:
        """Persist a JSON state snapshot for *run_id*.

        Overwrites any previously saved snapshot for the same run.
        """
        run = self.db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if run is None:
            raise ValueError(f"Run {run_id} not found")
        run.state_snapshot = json.dumps(state, default=str)
        self.db.commit()

    def get_snapshot(self, run_id: int) -> dict[str, Any] | None:
        """Return the saved state snapshot for *run_id*, or ``None``."""
        run = self.db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if run is None or run.state_snapshot is None:
            return None
        try:
            return json.loads(run.state_snapshot)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to decode state snapshot for run %d: %s", run_id, exc)
            return None

    # ── Replay buffer ───────────────────────────────────────────────────

    def get_replay_buffer(self, run_id: int, last_n: int = _DEFAULT_REPLAY_N) -> list[dict[str, Any]]:
        """Return the last *last_n* steps for *run_id* as dicts.

        Steps are ordered oldest-first (chronological).
        """
        from backend.app.models.cognition.agent import AgentStep

        steps = (
            self.db.query(AgentStep)
            .filter(AgentStep.run_id == run_id)
            .order_by(AgentStep.step_number.desc())
            .limit(last_n)
            .all()
        )
        # Reverse so oldest is first
        steps.reverse()
        return [
            {
                "step_number": s.step_number,
                "action": s.action,
                "action_input": self._safe_json_load(s.action_input_json),
                "observation": s.observation,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in steps
        ]

    @staticmethod
    def _safe_json_load(value: str | None) -> Any:
        if not value:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
