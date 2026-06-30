"""Tests for v1.04 P03 system health service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.services.awareness.health_monitor import SystemHealthService


class TestSystemHealthService:
    def test_check_healthy_service(self, db_session: Session) -> None:
        """A service that doesn't raise is healthy."""

        def healthy_check() -> None:
            pass

        service = SystemHealthService(db_session)
        health = service.check_service("test_service", healthy_check)

        assert health.status == "healthy"
        assert health.response_time_ms >= 0
        assert health.error_message is None

    def test_check_down_service(self, db_session: Session) -> None:
        """A service that raises is down."""

        def failing_check() -> None:
            raise ConnectionError("Cannot connect to database")

        service = SystemHealthService(db_session)
        health = service.check_service("failing_service", failing_check)

        assert health.status == "down"
        assert "Cannot connect" in (health.error_message or "")

    def test_health_upsert(self, db_session: Session) -> None:
        """Re-checking updates existing record (upsert)."""

        def check() -> None:
            pass

        service = SystemHealthService(db_session)
        h1 = service.check_service("my_service", check)
        first_id = h1.id

        h2 = service.check_service("my_service", check)
        assert h2.id == first_id

    def test_get_all_health(self, db_session: Session) -> None:
        """Get all health records returns list."""

        def check() -> None:
            pass

        service = SystemHealthService(db_session)
        service.check_service("svc_a", check)
        service.check_service("svc_b", check)

        all_health = service.get_all_health()
        assert len(all_health) == 2

    def test_get_service_health(self, db_session: Session) -> None:
        """Get specific service health returns correct record."""

        def check() -> None:
            pass

        service = SystemHealthService(db_session)
        service.check_service("specific_svc", check)

        result = service.get_service_health("specific_svc")
        assert result is not None
        assert result.service_name == "specific_svc"
        assert result.status == "healthy"

    def test_get_service_health_not_found(self, db_session: Session) -> None:
        """Getting health for non-existent service returns None."""
        service = SystemHealthService(db_session)
        result = service.get_service_health("nonexistent")
        assert result is None

    def test_get_overall_status_healthy(self, db_session: Session) -> None:
        """Overall status is healthy when all services are healthy."""

        def check() -> None:
            pass

        service = SystemHealthService(db_session)
        service.check_service("svc1", check)
        service.check_service("svc2", check)

        overall = service.get_overall_status()
        assert overall["overall_status"] == "healthy"
        assert overall["healthy"] == 2
        assert overall["down"] == 0

    def test_get_overall_status_down(self, db_session: Session) -> None:
        """Overall status is down when any service is down."""

        def check() -> None:
            pass

        def fail() -> None:
            raise RuntimeError("boom")

        service = SystemHealthService(db_session)
        service.check_service("good_svc", check)
        service.check_service("bad_svc", fail)

        overall = service.get_overall_status()
        assert overall["overall_status"] == "down"
        assert overall["down"] == 1

    def test_get_overall_status_empty(self, db_session: Session) -> None:
        """Overall status with no services returns unknown."""
        service = SystemHealthService(db_session)
        overall = service.get_overall_status()
        assert overall["overall_status"] == "unknown"
        assert overall["services"] == 0
