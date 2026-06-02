from sqlalchemy import select

from backend.app.ai.memory.models import Memory
from backend.app.db.session import SessionLocal


class MemoryRepository:

    def add(
        self,
        user_id: int,
        query: str,
        response: str
    ) -> None:

        with SessionLocal() as db:

            memory = Memory(
                user_id=user_id,
                query=query,
                response=response
            )

            db.add(memory)
            db.commit()

    def search(
        self,
        user_id: int,
        query: str
    ) -> str | None:

        query_words = [
            word.lower()
            for word in query.split()
            if len(word) > 3
        ]

        if not query_words:
            return None

        with SessionLocal() as db:

            stmt = (
                select(Memory)
                .where(Memory.user_id == user_id)
                .order_by(Memory.created_at.desc())
                .limit(50)
            )

            memories = db.execute(stmt).scalars().all()

            for memory in memories:

                memory_query = memory.query.lower()

                if any(
                    word in memory_query
                    for word in query_words
                ):

                    return (
                        f"[Memory Recall]\n"
                        f"Previous Question: {memory.query}\n"
                        f"Previous Answer: {memory.response}"
                    )

        return None

    def count(self) -> int:

        with SessionLocal() as db:
            return db.query(Memory).count()