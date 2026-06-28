"""System health monitor — tracks service health status, response time, and errors."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.awareness.system_health import SystemHealth

# Threshold for degraded status (ms)
DEGRADED_THRESHOLD_MS = 2000

# Max error message length stored in DB
MAX_ERROR_LENGTH = 500


class SystemHealthService:
    """System health monitoring service."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def check_service(
        self,
        service_name: str,
        check_func: Callable[[], None],
    ) -> SystemHealth:
        """Check a service's health by running *check_func*.

        Args:
            service_name: Name of the service.
            check_func: Callable that raises on failure.

        Returns:
            Updated SystemHealth record.
        """
        start_time = time.monotonic()
        try:
            check_func()
            response_time = int((time.monotonic() - start_time) * 1000)
            status = "healthy"
            error_message: str | None = None
        except Exception as exc:
            response_time = int((time.monotonic() - start_time) * 1000)
            status = "down"
            error_message = str(exc)[:MAX_ERROR_LENGTH]

        if status == "healthy" and response_time > DEGRADED_THRESHOLD_MS:
            status = "degraded"

        existing = self.db.query(SystemHealth).filter(SystemHealth.service_name == service_name).first()

        if existing is not None:
            existing.status = status
            existing.response_time_ms = response_time
            existing.error_message = error_message
            existing.last_check = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        health = SystemHealth(
            service_name=service_name,
            status=status,
            response_time_ms=response_time,
            error_message=error_message,
            last_check=datetime.now(),
        )
        self.db.add(health)
        self.db.commit()
        self.db.refresh(health)
        return health

    def check_all_services(
        self,
        checks: dict[str, Callable[[], None]],
    ) -> list[SystemHealth]:
        """Check all registered services sequentially."""
        results: list[SystemHealth] = []
        for service_name, check_func in checks.items():
            results.append(self.check_service(service_name, check_func))
        return results

    def get_all_health(self) -> list[SystemHealth]:
        """Get health status of all services."""
        return list(self.db.query(SystemHealth).all())

    def get_service_health(self, service_name: str) -> SystemHealth | None:
        """Get health status of a specific service."""
        return self.db.query(SystemHealth).filter(SystemHealth.service_name == service_name).first()

    def get_overall_status(self) -> dict[str, object]:
        """Get overall system health summary."""
        services = self.db.query(SystemHealth).all()

        if not services:
            return {
                "overall_status": "unknown",
                "services": 0,
                "healthy": 0,
                "degraded": 0,
                "down": 0,
            }

        healthy = sum(1 for s in services if s.status == "healthy")
        degraded = sum(1 for s in services if s.status == "degraded")
        down = sum(1 for s in services if s.status == "down")

        if down > 0:
            overall = "down"
        elif degraded > 0:
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "overall_status": overall,
            "services": len(services),
            "healthy": healthy,
            "degraded": degraded,
            "down": down,
        }
