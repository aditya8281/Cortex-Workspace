"""Standalone health checks for system components."""

import logging

from sqlalchemy import text

from backend.app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class HealthService:
    @staticmethod
    def check_database() -> bool:
        """
        Fast, fail-safe DB readiness check.
        Executes a trivial query in a short-lived thread and times out quickly
        to avoid request hangs if the underlying driver/filesystem is blocked.
        """
        import threading

        result = {"ok": False}

        def _probe():
            try:
                db = SessionLocal()
                try:
                    db.execute(text("SELECT 1"))
                    result["ok"] = True
                finally:
                    db.close()
            except Exception:
                result["ok"] = False

        t = threading.Thread(target=_probe, daemon=True)
        t.start()
        t.join(timeout=2.0)
        return bool(result["ok"])

    @staticmethod
    def check_redis() -> bool:
        """Check Redis connectivity."""
        try:
            import redis

            from backend.app.core.config import settings

            r = redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
            r.ping()
            return True
        except Exception as e:
            logger.debug("Redis health check failed: %s", e)
            return False

    @staticmethod
    def check_ollama() -> bool:
        """Check Ollama server availability."""
        try:
            import httpx

            from backend.app.core.config import settings

            resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3.0)
            return resp.status_code == 200
        except Exception as e:
            logger.debug("Ollama health check failed: %s", e)
            return False

    @staticmethod
    def check_qdrant() -> bool:
        """Check Qdrant vector DB availability."""
        try:
            import httpx

            from backend.app.core.config import settings

            qdrant_url = getattr(settings, "QDRANT_URL", "http://localhost:6333")
            resp = httpx.get(f"{qdrant_url}/collections", timeout=3.0)
            return resp.status_code == 200
        except Exception as e:
            logger.debug("Qdrant health check failed: %s", e)
            return False

    @staticmethod
    def check_all() -> dict:
        """Run all health checks and return results."""
        db_ok = HealthService.check_database()
        redis_ok = HealthService.check_redis()
        ollama_ok = HealthService.check_ollama()
        qdrant_ok = HealthService.check_qdrant()

        all_ok = all([db_ok, redis_ok, ollama_ok, qdrant_ok])
        any_ok = any([db_ok, redis_ok, ollama_ok, qdrant_ok])

        if all_ok:
            status = "healthy"
        elif any_ok:
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "checks": {
                "database": db_ok,
                "redis": redis_ok,
                "ollama": ollama_ok,
                "qdrant": qdrant_ok,
            },
        }
