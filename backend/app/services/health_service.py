"""Standalone health checks for system components."""

from sqlalchemy import text

from backend.app.db.session import SessionLocal


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
