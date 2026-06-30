"""Tests for SystemMonitorService."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.services.awareness.system_monitor import SystemMonitorService


class TestSystemMonitorService:
    def test_take_snapshot(self, db_session: Session) -> None:
        """Taking a snapshot returns a record with valid metrics."""
        svc = SystemMonitorService(db_session)
        snap = svc.take_snapshot(user_id=1)
        assert snap.id is not None
        assert snap.cpu_percent >= 0
        assert snap.memory_percent >= 0
        assert snap.disk_percent >= 0
        assert snap.user_id == 1

    def test_take_snapshot_no_user(self, db_session: Session) -> None:
        """Taking a snapshot without a user_id leaves it None."""
        svc = SystemMonitorService(db_session)
        snap = svc.take_snapshot()
        assert snap.user_id is None
        assert snap.cpu_percent >= 0
        assert snap.memory_percent >= 0
        assert snap.disk_percent >= 0

    def test_take_snapshot_records_network(self, db_session: Session) -> None:
        """Snapshot captures network byte counters."""
        svc = SystemMonitorService(db_session)
        snap = svc.take_snapshot(user_id=1)
        assert snap.network_sent_bytes >= 0
        assert snap.network_recv_bytes >= 0

    def test_take_snapshot_records_load_average(self, db_session: Session) -> None:
        """Snapshot captures load averages."""
        svc = SystemMonitorService(db_session)
        snap = svc.take_snapshot(user_id=1)
        assert snap.load_average_1m >= 0
        assert snap.load_average_5m >= 0
        assert snap.load_average_15m >= 0

    def test_get_recent_snapshots(self, db_session: Session) -> None:
        """Getting recent snapshots returns all stored records."""
        svc = SystemMonitorService(db_session)
        svc.take_snapshot(user_id=1)
        svc.take_snapshot(user_id=1)
        snaps = svc.get_recent_snapshots(user_id=1, limit=10)
        assert len(snaps) == 2

    def test_get_recent_snapshots_empty(self, db_session: Session) -> None:
        """Getting recent snapshots with no data returns empty list."""
        svc = SystemMonitorService(db_session)
        snaps = svc.get_recent_snapshots(user_id=1)
        assert snaps == []

    def test_get_recent_snapshots_respects_limit(self, db_session: Session) -> None:
        """Getting recent snapshots respects the limit parameter."""
        svc = SystemMonitorService(db_session)
        for _ in range(5):
            svc.take_snapshot(user_id=1)
        snaps = svc.get_recent_snapshots(user_id=1, limit=2)
        assert len(snaps) == 2

    def test_get_recent_snapshots_user_isolation(self, db_session: Session) -> None:
        """Getting recent snapshots is isolated by user_id."""
        svc = SystemMonitorService(db_session)
        svc.take_snapshot(user_id=1)
        svc.take_snapshot(user_id=2)
        snaps_user1 = svc.get_recent_snapshots(user_id=1)
        snaps_user2 = svc.get_recent_snapshots(user_id=2)
        assert len(snaps_user1) == 1
        assert len(snaps_user2) == 1
        assert snaps_user1[0].user_id == 1
        assert snaps_user2[0].user_id == 2

    def test_detect_anomalies_empty(self, db_session: Session) -> None:
        """Detecting anomalies with no snapshots returns empty list."""
        svc = SystemMonitorService(db_session)
        anomalies = svc.detect_anomalies()
        assert anomalies == []

    def test_detect_anomalies_none(self, db_session: Session) -> None:
        """Detecting anomalies with normal thresholds returns a list (possibly empty)."""
        svc = SystemMonitorService(db_session)
        svc.take_snapshot()
        anomalies = svc.detect_anomalies(threshold_cpu=99, threshold_memory=99, threshold_disk=99)
        # May or may not have anomalies depending on system state
        assert isinstance(anomalies, list)

    def test_detect_anomalies_high_thresholds_no_flags(self, db_session: Session) -> None:
        """Very high thresholds should not flag normal system metrics."""
        svc = SystemMonitorService(db_session)
        svc.take_snapshot(user_id=1)
        anomalies = svc.detect_anomalies(threshold_cpu=100, threshold_memory=100, threshold_disk=100)
        assert anomalies == []

    def test_detect_anomalies_low_thresholds_flag(self, db_session: Session) -> None:
        """Very low thresholds should flag the current system metrics."""
        svc = SystemMonitorService(db_session)
        svc.take_snapshot(user_id=1)
        anomalies = svc.detect_anomalies(threshold_cpu=0.0, threshold_memory=0.0, threshold_disk=0.0)
        assert len(anomalies) == 3
        types = {a["type"] for a in anomalies}
        assert types == {"high_cpu", "high_memory", "high_disk"}

    def test_take_snapshot_commits_to_db(self, db_session: Session) -> None:
        """Snapshots are persisted and queryable from the database."""
        svc = SystemMonitorService(db_session)
        snap = svc.take_snapshot(user_id=1)
        from backend.app.models.awareness.system_snapshot import SystemSnapshot
        found = db_session.query(SystemSnapshot).filter(SystemSnapshot.id == snap.id).first()
        assert found is not None
        assert found.cpu_percent == snap.cpu_percent
