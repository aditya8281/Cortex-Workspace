"""Tests for v1.03 P02 — episodic and semantic memory services."""

from __future__ import annotations

from backend.app.schemas.memory.episodic import EpisodicMemoryCreate, EpisodicMemoryUpdate
from backend.app.schemas.memory.semantic import SemanticMemoryCreate, SemanticMemoryUpdate
from backend.app.services.memory import MemoryServiceFactory


class TestEpisodicService:
    """EpisodicMemoryService tests."""

    def test_create(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        data = EpisodicMemoryCreate(content="Test experience", importance=0.8)
        memory = service.create(1, data)
        assert memory.id is not None
        assert memory.content == "Test experience"
        assert memory.importance == 0.8
        assert memory.confidence == 0.5
        assert memory.access_count == 0
        assert memory.recency_score == 1.0

    def test_create_with_context(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        data = EpisodicMemoryCreate(
            content="Debugged a leak",
            context={"source": "terminal", "trigger": "error"},
            emotion="frustrated",
            importance=0.7,
        )
        memory = service.create(1, data)
        assert memory.context == {"source": "terminal", "trigger": "error"}
        assert memory.emotion == "frustrated"

    def test_retrieve_increments_access(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        data = EpisodicMemoryCreate(content="Accessed memory")
        memory = service.create(1, data)

        retrieved = service.retrieve(1, memory.id)
        assert retrieved.access_count == 1
        assert retrieved.last_accessed is not None

        retrieved2 = service.retrieve(1, memory.id)
        assert retrieved2.access_count == 2

    def test_retrieve_wrong_user(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        memory = service.create(1, EpisodicMemoryCreate(content="Private"))
        result = service.retrieve(2, memory.id)
        assert result is None

    def test_list_recent(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        for i in range(15):
            service.create(1, EpisodicMemoryCreate(content=f"Mem {i}"))

        memories, total = service.list_recent(1, limit=10, offset=0)
        assert len(memories) == 10
        assert total == 15

        memories2, total2 = service.list_recent(1, limit=10, offset=10)
        assert len(memories2) == 5

    def test_list_by_importance(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        service.create(1, EpisodicMemoryCreate(content="Low", importance=0.2))
        service.create(1, EpisodicMemoryCreate(content="High", importance=0.9))

        high = service.list_by_importance(1, min_importance=0.5)
        assert len(high) == 1
        assert high[0].content == "High"

    def test_update(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        memory = service.create(1, EpisodicMemoryCreate(content="Original", importance=0.5))

        updated = service.update(1, memory.id, EpisodicMemoryUpdate(content="Updated"))
        assert updated.content == "Updated"
        assert updated.importance == 0.5  # Unchanged

    def test_update_nonexistent(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        result = service.update(1, 999, EpisodicMemoryUpdate(content="X"))
        assert result is None

    def test_delete(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        memory = service.create(1, EpisodicMemoryCreate(content="To delete"))
        deleted = service.delete(1, memory.id)
        assert deleted is True

        result = service.retrieve(1, memory.id)
        assert result is None

    def test_delete_nonexistent(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        deleted = service.delete(1, 999)
        assert deleted is False

    def test_search_content(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        service.create(1, EpisodicMemoryCreate(content="Python debugging"))
        service.create(1, EpisodicMemoryCreate(content="JavaScript refactoring"))
        service.create(1, EpisodicMemoryCreate(content="Python deployment"))

        results = service.search_content(1, "Python")
        assert len(results) == 2

    def test_user_isolation(self, db_session):
        service = MemoryServiceFactory(db_session).episodic
        service.create(1, EpisodicMemoryCreate(content="User 1 memory"))
        service.create(2, EpisodicMemoryCreate(content="User 2 memory"))

        u1, total1 = service.list_recent(1)
        assert total1 == 1
        assert u1[0].content == "User 1 memory"


class TestSemanticService:
    """SemanticMemoryService tests."""

    def test_create(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        data = SemanticMemoryCreate(content="Dark theme preferred", category="preference", source="user_input")
        memory = service.create(1, data)
        assert memory.id is not None
        assert memory.category == "preference"
        assert memory.confidence == 0.5

    def test_dedup_identical_content(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        data = SemanticMemoryCreate(content="FastAPI is the backend")

        m1 = service.create(1, data)
        assert m1.confidence == 0.5

        m2 = service.create(1, data)
        assert m2.id == m1.id
        assert m2.confidence == 0.6

    def test_dedup_different_users(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        data = SemanticMemoryCreate(content="Shared fact")

        m1 = service.create(1, data)
        m2 = service.create(2, data)
        assert m1.id != m2.id  # Different users don't dedup

    def test_retrieve_increments_access(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        memory = service.create(1, SemanticMemoryCreate(content="Access me"))

        retrieved = service.retrieve(1, memory.id)
        assert retrieved.access_count == 1
        assert retrieved.last_accessed is not None

    def test_list_by_category(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        service.create(1, SemanticMemoryCreate(content="Dark theme", category="preference"))
        service.create(1, SemanticMemoryCreate(content="Python is fast", category="fact"))
        service.create(1, SemanticMemoryCreate(content="Vim preferred", category="preference"))

        prefs = service.list_by_category(1, "preference")
        assert len(prefs) == 2

        facts = service.list_by_category(1, "fact")
        assert len(facts) == 1

    def test_list_all(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        for i in range(12):
            service.create(1, SemanticMemoryCreate(content=f"Fact {i}"))

        memories, total = service.list_all(1, limit=10, offset=0)
        assert len(memories) == 10
        assert total == 12

    def test_search_content(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        service.create(1, SemanticMemoryCreate(content="Python is great"))
        service.create(1, SemanticMemoryCreate(content="Java is okay"))
        service.create(1, SemanticMemoryCreate(content="Python deployment"))

        results = service.search_content(1, "Python")
        assert len(results) == 2

    def test_update(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        memory = service.create(1, SemanticMemoryCreate(content="Original", category="fact"))

        updated = service.update(1, memory.id, SemanticMemoryUpdate(content="Updated"))
        assert updated.content == "Updated"
        assert updated.category == "fact"  # Unchanged

    def test_delete(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        memory = service.create(1, SemanticMemoryCreate(content="To delete"))
        deleted = service.delete(1, memory.id)
        assert deleted is True

        result = service.retrieve(1, memory.id)
        assert result is None

    def test_get_categories(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        service.create(1, SemanticMemoryCreate(content="A", category="preference"))
        service.create(1, SemanticMemoryCreate(content="B", category="preference"))
        service.create(1, SemanticMemoryCreate(content="C", category="fact"))

        categories = service.get_categories(1)
        assert len(categories) == 2

        pref_count = next(c["count"] for c in categories if c["category"] == "preference")
        assert pref_count == 2

    def test_user_isolation(self, db_session):
        service = MemoryServiceFactory(db_session).semantic
        service.create(1, SemanticMemoryCreate(content="User 1 fact"))
        service.create(2, SemanticMemoryCreate(content="User 2 fact"))

        u1, total1 = service.list_all(1)
        assert total1 == 1


class TestServiceFactory:
    """MemoryServiceFactory tests."""

    def test_creates_services(self, db_session):
        factory = MemoryServiceFactory(db_session)
        assert factory.episodic is not None
        assert factory.semantic is not None

    def test_reuses_instances(self, db_session):
        factory = MemoryServiceFactory(db_session)
        assert factory.episodic is factory.episodic
        assert factory.semantic is factory.semantic
