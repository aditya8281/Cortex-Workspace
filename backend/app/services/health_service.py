"""Standalone health checks for system components."""

from sqlalchemy import text

from backend.app.db.session import SessionLocal
from backend.app.ai.memory.repository import MemoryRepository


class HealthService:

    @staticmethod
    def check_database() -> bool:
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return True
        except Exception:
            return False

    @staticmethod
    def check_memory() -> bool:
        try:
            MemoryRepository()
            return True
        except Exception:
            return False
