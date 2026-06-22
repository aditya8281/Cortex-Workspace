"""Standalone health checks for system components."""

import logging
import urllib.request
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
        """Check Redis connectivity with a short timeout."""
        import threading

        result = {"ok": False}

        def _probe():
            try:
                from backend.app.core.redis import redis_cache
                import asyncio

                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(redis_cache.ping())
                    result["ok"] = True
                finally:
                    loop.close()
            except Exception as e:
                logger.debug("Redis health check failed: %s", e)
                result["ok"] = False

        t = threading.Thread(target=_probe, daemon=True)
        t.start()
        t.join(timeout=2.0)
        return bool(result["ok"])

    @staticmethod
    def check_ollama() -> bool:
        """Check Ollama API availability with a short timeout."""
        import threading

        result = {"ok": False}

        def _probe():
            try:
                from backend.app.core.config import settings
                req = urllib.request.Request(
                    f"{settings.OLLAMA_BASE_URL}/api/tags",
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    result["ok"] = resp.status == 200
            except Exception as e:
                logger.debug("Ollama health check failed: %s", e)
                result["ok"] = False

        t = threading.Thread(target=_probe, daemon=True)
        t.start()
        t.join(timeout=3.0)
        return bool(result["ok"])
