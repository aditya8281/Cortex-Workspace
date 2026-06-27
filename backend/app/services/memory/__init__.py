"""CORTEX memory domain services."""

from backend.app.services.memory.episodic import EpisodicMemoryService
from backend.app.services.memory.semantic import SemanticMemoryService


class MemoryServiceFactory:
    """Factory for creating memory services with shared database session.

    Usage:
        factory = MemoryServiceFactory(db)
        episodic_memory = await factory.episodic.create(user_id, data)
        semantic_memory = await factory.semantic.create(user_id, data)
    """

    def __init__(self, db: object) -> None:
        self._db = db
        self._episodic: EpisodicMemoryService | None = None
        self._semantic: SemanticMemoryService | None = None

    @property
    def episodic(self) -> EpisodicMemoryService:
        if self._episodic is None:
            self._episodic = EpisodicMemoryService(self._db)
        return self._episodic

    @property
    def semantic(self) -> SemanticMemoryService:
        if self._semantic is None:
            self._semantic = SemanticMemoryService(self._db)
        return self._semantic
