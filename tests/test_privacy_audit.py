"""Tests for v1.05 P03 audit logging service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.services.privacy.audit import AuditLoggingService


class TestAuditLoggingService:
    def test_log_creates_record(self, db_session: Session) -> None:
        service = AuditLoggingService(db_session)
        log = service.log(
            user_id=1,
            action="create",
            resource_type="memory",
            resource_id=42,
            details={"key": "value"},
            ip_address="127.0.0.1",
        )
        assert log.id is not None
        assert log.user_id == 1
        assert log.action == "create"
        assert log.success == 1
        assert log.timestamp is not None

    def test_log_failure(self, db_session: Session) -> None:
        service = AuditLoggingService(db_session)
        log = service.log(
            user_id=1,
            action="delete",
            resource_type="file",
            success=False,
            error_message="File not found",
        )
        assert log.success == 0
        assert log.error_message == "File not found"

    def test_get_user_logs(self, db_session: Session) -> None:
        service = AuditLoggingService(db_session)
        for _ in range(5):
            service.log(user_id=1, action="read", resource_type="file")
        service.log(user_id=2, action="read", resource_type="file")
        logs = service.get_user_logs(user_id=1, limit=10)
        assert len(logs) == 5
        assert logs[0].timestamp >= logs[-1].timestamp

    def test_get_user_logs_with_filters(self, db_session: Session) -> None:
        service = AuditLoggingService(db_session)
        service.log(user_id=1, action="create", resource_type="memory")
        service.log(user_id=1, action="read", resource_type="file")
        service.log(user_id=1, action="delete", resource_type="memory")
        logs = service.get_user_logs(user_id=1, action_filter="create")
        assert len(logs) == 1
        logs = service.get_user_logs(user_id=1, resource_type_filter="memory")
        assert len(logs) == 2

    def test_get_user_logs_with_time_range(self, db_session: Session) -> None:
        service = AuditLoggingService(db_session)
        service.log(user_id=1, action="read", resource_type="file")
        now = datetime.now(timezone.utc)
        logs = service.get_user_logs(
            user_id=1,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
        )
        assert len(logs) == 1

    def test_get_resource_logs(self, db_session: Session) -> None:
        service = AuditLoggingService(db_session)
        service.log(user_id=1, action="create", resource_type="memory", resource_id=42)
        service.log(user_id=2, action="read", resource_type="memory", resource_id=42)
        service.log(user_id=1, action="update", resource_type="memory", resource_id=43)
        logs = service.get_resource_logs("memory", 42)
        assert len(logs) == 2

    def test_action_stats(self, db_session: Session) -> None:
        service = AuditLoggingService(db_session)
        service.log(user_id=1, action="create", resource_type="memory")
        service.log(user_id=1, action="read", resource_type="memory")
        service.log(user_id=1, action="read", resource_type="file")
        stats = service.get_action_stats(user_id=1, days=30)
        assert stats["total_actions"] == 3
        assert stats["action_breakdown"]["read"] == 2
        assert stats["action_breakdown"]["create"] == 1
        assert stats["success_count"] == 3

    def test_count_user_logs(self, db_session: Session) -> None:
        service = AuditLoggingService(db_session)
        service.log(user_id=1, action="read", resource_type="file")
        service.log(user_id=1, action="read", resource_type="file")
        assert service.count_user_logs(user_id=1) == 2

    def test_delete_old_logs(self, db_session: Session) -> None:
        service = AuditLoggingService(db_session)
        service.log(user_id=1, action="read", resource_type="file")
        assert service.delete_old_logs(retention_days=90) >= 0
