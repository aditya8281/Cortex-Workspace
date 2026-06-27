"""CORTEX memory domain services."""

from backend.app.services.memory.auto_connect import AutoConnectionService
from backend.app.services.memory.decay import ForgettingService
from backend.app.services.memory.episodic import EpisodicMemoryService
from backend.app.services.memory.memory_graph_service import MemoryGraphService
from backend.app.services.memory.memory_search import MemorySearchService
from backend.app.services.memory.semantic import SemanticMemoryService
from backend.app.services.memory.working import WorkingMemoryService


class MemoryServiceFactory:
    """Factory for creating memory services with shared database session.

    Usage:
        factory = MemoryServiceFactory(db)
        episodic_memory = factory.episodic.create(user_id, data)
        semantic_memory = factory.semantic.create(user_id, data)
        working_memory = factory.working.add(user_id, session_id, content)
        graph_node = factory.graph.add_node(user_id, "episodic", mem_id, label)
        auto_edges = factory.auto_connect.connect_related(user_id, "episodic", mem_id, content)
        search_results = factory.search.search(user_id, query)
        forgetting_stats = factory.forgetting.get_forgetting_stats(user_id)
    """

    def __init__(self, db: object) -> None:
        self._db = db
        self._episodic: EpisodicMemoryService | None = None
        self._semantic: SemanticMemoryService | None = None
        self._working: WorkingMemoryService | None = None
        self._graph: MemoryGraphService | None = None
        self._auto_connect: AutoConnectionService | None = None
        self._search: MemorySearchService | None = None
        self._forgetting: ForgettingService | None = None

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

    @property
    def working(self) -> WorkingMemoryService:
        if self._working is None:
            self._working = WorkingMemoryService(self._db)
        return self._working

    @property
    def graph(self) -> MemoryGraphService:
        if self._graph is None:
            self._graph = MemoryGraphService(self._db)
        return self._graph

    @property
    def auto_connect(self) -> AutoConnectionService:
        if self._auto_connect is None:
            self._auto_connect = AutoConnectionService(self._db)
        return self._auto_connect

    @property
    def search(self) -> MemorySearchService:
        if self._search is None:
            self._search = MemorySearchService(self._db)
        return self._search

    @property
    def forgetting(self) -> ForgettingService:
        if self._forgetting is None:
            self._forgetting = ForgettingService(self._db)
        return self._forgetting
