from sqlalchemy import text

from backend.app.db.session import SessionLocal
from backend.app.ai.memory.repository import MemoryRepository
from backend.app.rag.service import RAGService
from backend.app.core.paths import PROJECT_ROOT


class HealthService:

    @staticmethod
    def check_database() -> bool:
        try:
            db = SessionLocal()

            db.execute(
                text("SELECT 1")
            )

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

    @staticmethod
    def check_rag() -> bool:
        try:
            rag = RAGService(
                str(PROJECT_ROOT)
            )

            return rag is not None

        except Exception:
            return False