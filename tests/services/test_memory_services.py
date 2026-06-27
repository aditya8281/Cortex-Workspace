"""Tests for v1.03 memory services — episodic, semantic, working, graph, auto-connect."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from backend.app.schemas.memory.episodic import EpisodicMemoryCreate, EpisodicMemoryUpdate
from backend.app.schemas.memory.semantic import SemanticMemoryCreate, SemanticMemoryUpdate
from backend.app.services.memory import MemoryServiceFactory
from backend.app.services.memory.auto_connect import AutoConnectionService
from backend.app.services.memory.memory_graph_service import MemoryGraphService
from backend.app.services.memory.temporal import TemporalScoring
from backend.app.services.memory.working import WorkingMemoryService

# ── Episodic ──────────────────────────────────────────────────


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
        assert updated.importance == 0.5

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


# ── Semantic ──────────────────────────────────────────────────


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
        assert m1.id != m2.id

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
        assert updated.category == "fact"

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


# ── Working Memory ────────────────────────────────────────────


class TestWorkingMemoryService:
    """WorkingMemoryService tests."""

    def test_add(self, db_session):
        service = WorkingMemoryService(db_session)
        item = service.add(user_id=1, session_id="s1", content="Current task", slot="active", priority=5)
        assert item.id is not None
        assert item.slot == "active"
        assert item.priority == 5
        assert item.expires_at > datetime.utcnow()

    def test_get_active_ordered_by_priority(self, db_session):
        service = WorkingMemoryService(db_session)
        service.add(user_id=1, session_id="s1", content="Low", priority=1)
        service.add(user_id=1, session_id="s1", content="High", priority=10)
        service.add(user_id=1, session_id="s1", content="Medium", priority=5)

        active = service.get_active(user_id=1, session_id="s1")
        assert len(active) == 3
        assert active[0].priority == 10
        assert active[1].priority == 5
        assert active[2].priority == 1

    def test_get_by_slot(self, db_session):
        service = WorkingMemoryService(db_session)
        service.add(user_id=1, session_id="s1", content="Active item", slot="active")
        service.add(user_id=1, session_id="s1", content="Buffer item", slot="buffer")
        service.add(user_id=1, session_id="s1", content="Archive item", slot="archive")

        active = service.get_by_slot(1, "s1", "active")
        assert len(active) == 1
        assert active[0].content == "Active item"

    def test_promote(self, db_session):
        service = WorkingMemoryService(db_session)
        item = service.add(user_id=1, session_id="s1", content="Buffer item", slot="buffer")

        result = service.promote(user_id=1, memory_id=item.id)
        assert result is True

        active = service.get_by_slot(1, "s1", "active")
        assert any(i.id == item.id for i in active)

    def test_promote_overflow_demotes_lowest(self, db_session):
        service = WorkingMemoryService(db_session)
        # Fill active to MAX_ACTIVE_ITEMS (20)
        for i in range(20):
            service.add(user_id=1, session_id="s1", content=f"Item {i}", slot="active", priority=i)
        buffer_item = service.add(user_id=1, session_id="s1", content="Promote me", slot="buffer", priority=100)

        service.promote(user_id=1, memory_id=buffer_item.id)
        active = service.get_by_slot(1, "s1", "active")
        # Should still be 20 (one was demoted)
        assert len(active) == 20

    def test_archive(self, db_session):
        service = WorkingMemoryService(db_session)
        item = service.add(user_id=1, session_id="s1", content="To archive")

        result = service.archive(user_id=1, memory_id=item.id)
        assert result is True

        archived = service.get_by_slot(1, "s1", "archive")
        assert any(i.id == item.id for i in archived)

    def test_demote(self, db_session):
        service = WorkingMemoryService(db_session)
        item = service.add(user_id=1, session_id="s1", content="Active", slot="active")

        result = service.demote(user_id=1, memory_id=item.id)
        assert result is True

        buffer = service.get_by_slot(1, "s1", "buffer")
        assert any(i.id == item.id for i in buffer)

    def test_remove(self, db_session):
        service = WorkingMemoryService(db_session)
        item = service.add(user_id=1, session_id="s1", content="Remove me")
        item_id = item.id

        result = service.remove(user_id=1, memory_id=item_id)
        assert result is True
        # Verify deleted via direct query
        from backend.app.models.memory.working import WorkingMemory

        assert db_session.query(WorkingMemory).filter(WorkingMemory.id == item_id).first() is None

    def test_remove_nonexistent(self, db_session):
        service = WorkingMemoryService(db_session)
        assert service.remove(user_id=1, memory_id=999) is False

    def test_cleanup_expired(self, db_session):
        service = WorkingMemoryService(db_session)
        service.add(user_id=1, session_id="s1", content="Valid")
        item = service.add(user_id=1, session_id="s1", content="Expired")

        # Force expire
        item.expires_at = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()

        count = service.cleanup_expired(user_id=1, session_id="s1")
        assert count == 1

    def test_clear_session(self, db_session):
        service = WorkingMemoryService(db_session)
        service.add(user_id=1, session_id="s1", content="A")
        service.add(user_id=1, session_id="s1", content="B")
        service.add(user_id=1, session_id="s1", content="C")

        count = service.clear_session(user_id=1, session_id="s1")
        assert count == 3
        assert len(service.get_active(user_id=1, session_id="s1")) == 0

    def test_session_isolation(self, db_session):
        service = WorkingMemoryService(db_session)
        service.add(user_id=1, session_id="s1", content="Session 1")
        service.add(user_id=1, session_id="s2", content="Session 2")

        s1 = service.get_active(1, "s1")
        s2 = service.get_active(1, "s2")
        assert len(s1) == 1
        assert len(s2) == 1
        assert s1[0].content == "Session 1"

    def test_get_session_summary(self, db_session):
        service = WorkingMemoryService(db_session)
        service.add(user_id=1, session_id="s1", content="A", slot="active")
        service.add(user_id=1, session_id="s1", content="B", slot="buffer")
        service.add(user_id=1, session_id="s1", content="C", slot="archive")

        summary = service.get_session_summary(user_id=1, session_id="s1")
        assert summary["active"] == 1
        assert summary["buffer"] == 1
        assert summary["archive"] == 1
        assert summary["total_items"] == 3


# ── Memory Graph ──────────────────────────────────────────────


class TestMemoryGraphService:
    """MemoryGraphService tests."""

    def test_add_node(self, db_session):
        service = MemoryGraphService(db_session)
        node = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="Test")
        assert node.id is not None
        assert node.memory_type == "episodic"

    def test_add_node_idempotent(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="A")
        n2 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="A")
        assert n1.id == n2.id

    def test_add_edge(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="A")
        n2 = service.add_node(user_id=1, memory_type="semantic", memory_id=1, label="B")

        edge = service.add_edge(source_id=n1.id, target_id=n2.id, edge_type="related_to", weight=0.7)
        assert edge.id is not None
        assert edge.weight == 0.7

    def test_add_edge_self_loop_raises(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="A")
        with pytest.raises(ValueError, match="Self-loops"):
            service.add_edge(source_id=n1.id, target_id=n1.id, edge_type="related_to")

    def test_add_edge_duplicate_strengthens(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="A")
        n2 = service.add_node(user_id=1, memory_type="semantic", memory_id=1, label="B")

        e1 = service.add_edge(source_id=n1.id, target_id=n2.id, edge_type="related_to", weight=0.5)
        e2 = service.add_edge(source_id=n1.id, target_id=n2.id, edge_type="related_to", weight=0.5)
        assert e1.id == e2.id
        assert e2.weight == 0.55

    def test_add_bidirectional_edge(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="A")
        n2 = service.add_node(user_id=1, memory_type="semantic", memory_id=1, label="B")

        service.add_edge(source_id=n1.id, target_id=n2.id, edge_type="related_to", bidirectional=True)
        edges = service.get_edges_for_node(n1.id)
        assert len(edges) == 2

    def test_strengthen_and_weaken_edge(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="A")
        n2 = service.add_node(user_id=1, memory_type="semantic", memory_id=1, label="B")
        edge = service.add_edge(source_id=n1.id, target_id=n2.id, edge_type="related_to", weight=0.5)

        service.strengthen_edge(edge.id, amount=0.2)
        strengthened = service.strengthen_edge(edge.id, amount=0)
        assert strengthened.weight == 0.7

        service.weaken_edge(edge.id, amount=0.3)
        weakened = service.strengthen_edge(edge.id, amount=0)
        assert abs(weakened.weight - 0.4) < 1e-9

    def test_get_connections_depth_1(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="Center")
        n2 = service.add_node(user_id=1, memory_type="semantic", memory_id=1, label="N1")
        n3 = service.add_node(user_id=1, memory_type="semantic", memory_id=2, label="N2")

        service.add_edge(source_id=n1.id, target_id=n2.id, edge_type="related_to")
        service.add_edge(source_id=n1.id, target_id=n3.id, edge_type="related_to")

        connections = service.get_connections(n1.id, depth=1)
        assert len(connections) == 2

    def test_get_connections_depth_2(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="Center")
        n2 = service.add_node(user_id=1, memory_type="semantic", memory_id=1, label="Hop1")
        n3 = service.add_node(user_id=1, memory_type="semantic", memory_id=2, label="Hop2")

        service.add_edge(source_id=n1.id, target_id=n2.id, edge_type="related_to")
        service.add_edge(source_id=n2.id, target_id=n3.id, edge_type="related_to")

        d1 = service.get_connections(n1.id, depth=1)
        assert len(d1) == 1

        d2 = service.get_connections(n1.id, depth=2)
        assert len(d2) == 2

    def test_find_path(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="Start")
        n2 = service.add_node(user_id=1, memory_type="semantic", memory_id=1, label="Middle")
        n3 = service.add_node(user_id=1, memory_type="semantic", memory_id=2, label="End")

        service.add_edge(source_id=n1.id, target_id=n2.id, edge_type="related_to")
        service.add_edge(source_id=n2.id, target_id=n3.id, edge_type="related_to")

        path = service.find_path(n1.id, n3.id)
        assert path is not None
        assert len(path) == 3
        assert path[0].id == n1.id
        assert path[2].id == n3.id

    def test_find_path_no_path(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="A")
        n2 = service.add_node(user_id=1, memory_type="semantic", memory_id=1, label="B")

        path = service.find_path(n1.id, n2.id)
        assert path is None

    def test_delete_node_cascades(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="A")
        n2 = service.add_node(user_id=1, memory_type="semantic", memory_id=1, label="B")
        service.add_edge(source_id=n1.id, target_id=n2.id, edge_type="related_to")

        deleted = service.delete_node(user_id=1, node_id=n1.id)
        assert deleted is True

        edges = service.get_edges_for_node(n2.id)
        assert len(edges) == 0

    def test_get_graph_stats(self, db_session):
        service = MemoryGraphService(db_session)
        n1 = service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="A")
        n2 = service.add_node(user_id=1, memory_type="semantic", memory_id=1, label="B")
        service.add_edge(source_id=n1.id, target_id=n2.id, edge_type="related_to", weight=0.6)

        stats = service.get_graph_stats(1)
        assert stats["total_nodes"] == 2
        assert stats["total_edges"] == 1
        assert stats["avg_edge_weight"] == 0.6
        assert stats["nodes_by_type"]["episodic"] == 1

    def test_user_isolation(self, db_session):
        service = MemoryGraphService(db_session)
        service.add_node(user_id=1, memory_type="episodic", memory_id=1, label="U1")
        service.add_node(user_id=2, memory_type="episodic", memory_id=1, label="U2")

        u1_nodes = service.get_user_nodes(1)
        assert len(u1_nodes) == 1
        assert u1_nodes[0].label == "U1"


# ── Auto-Connection ───────────────────────────────────────────


class TestAutoConnectionService:
    """AutoConnectionService tests."""

    def test_connect_related_finds_keyword_matches(self, db_session):
        from backend.app.schemas.memory.episodic import EpisodicMemoryCreate
        from backend.app.services.memory.episodic import EpisodicMemoryService

        episodic = EpisodicMemoryService(db_session)
        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Python debugging session with memory leak"))
        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="JavaScript refactoring project"))

        auto = AutoConnectionService(db_session)
        # memory_id=999 doesn't exclude existing memories from search
        edges = auto.connect_related(
            user_id=1, memory_type="episodic", memory_id=999, content="Python performance optimization"
        )
        assert len(edges) >= 1

    def test_extract_keywords(self, db_session):
        auto = AutoConnectionService(db_session)
        keywords = auto._extract_keywords("The quick brown fox jumps over the lazy dog")
        assert "quick" in keywords
        assert "brown" in keywords
        assert "fox" in keywords
        assert "the" not in keywords
        assert "dog" in keywords

    def test_connect_related_no_keywords(self, db_session):
        auto = AutoConnectionService(db_session)
        edges = auto.connect_related(
            user_id=1,
            memory_type="episodic",
            memory_id=1,
            content="a an the is",  # All stop words
        )
        assert edges == []

    def test_connect_related_max_connections(self, db_session):
        from backend.app.schemas.memory.episodic import EpisodicMemoryCreate
        from backend.app.services.memory.episodic import EpisodicMemoryService

        episodic = EpisodicMemoryService(db_session)
        for i in range(10):
            episodic.create(user_id=1, data=EpisodicMemoryCreate(content=f"Python coding session number {i}"))

        auto = AutoConnectionService(db_session)
        edges = auto.connect_related(
            user_id=1,
            memory_type="episodic",
            memory_id=1,
            content="Python optimization",
            max_connections=3,
        )
        assert len(edges) <= 3


# ── Factory ───────────────────────────────────────────────────


class TestServiceFactory:
    """MemoryServiceFactory tests."""

    def test_creates_all_services(self, db_session):
        factory = MemoryServiceFactory(db_session)
        assert factory.episodic is not None
        assert factory.semantic is not None
        assert factory.working is not None
        assert factory.graph is not None
        assert factory.auto_connect is not None
        assert factory.search is not None
        assert factory.forgetting is not None

    def test_reuses_instances(self, db_session):
        factory = MemoryServiceFactory(db_session)
        assert factory.episodic is factory.episodic
        assert factory.semantic is factory.semantic
        assert factory.working is factory.working
        assert factory.graph is factory.graph
        assert factory.auto_connect is factory.auto_connect
        assert factory.search is factory.search
        assert factory.forgetting is factory.forgetting


# ── Temporal Scoring ──────────────────────────────────────────


class TestTemporalScoring:
    """TemporalScoring unit tests (no DB needed)."""

    def test_recency_score_recent(self):
        now = datetime.utcnow()
        score = TemporalScoring.recency_score(
            created_at=now - timedelta(days=1),
            last_accessed=now,
        )
        assert score > 0.8

    def test_recency_score_old(self):
        now = datetime.utcnow()
        score = TemporalScoring.recency_score(
            created_at=now - timedelta(days=90),
            last_accessed=now - timedelta(days=60),
        )
        assert score < 0.3

    def test_recency_score_no_access(self):
        now = datetime.utcnow()
        score = TemporalScoring.recency_score(
            created_at=now - timedelta(days=30),
            last_accessed=None,
        )
        assert 0.3 < score < 0.7

    def test_importance_weight(self):
        assert TemporalScoring.importance_weight(1.0, 1.0) == 1.0
        assert TemporalScoring.importance_weight(0.5, 0.5) == 0.25
        assert TemporalScoring.importance_weight(0.0, 1.0) == 0.0

    def test_access_frequency_weight(self):
        assert TemporalScoring.access_frequency_weight(0) == 0.0
        assert TemporalScoring.access_frequency_weight(1) > 0.0
        assert TemporalScoring.access_frequency_weight(100) > 0.4
        assert TemporalScoring.access_frequency_weight(1000) > 0.6

    def test_time_of_day_similarity(self):
        same = datetime(2026, 1, 2, 14, 30, 0)
        different = datetime(2026, 1, 1, 2, 0, 0)
        now = datetime(2026, 1, 1, 14, 0, 0)

        assert TemporalScoring.time_of_day_similarity(now, same) > 0.9
        assert TemporalScoring.time_of_day_similarity(now, different) < 0.2

    def test_composite_temporal_score(self):
        now = datetime.utcnow()
        score = TemporalScoring.composite_temporal_score(
            created_at=now - timedelta(days=1),
            last_accessed=now,
            importance=0.8,
            confidence=0.9,
            access_count=10,
        )
        assert 0.0 <= score <= 1.0
        assert score > 0.5


# ── Memory Search ─────────────────────────────────────────────


class TestMemorySearchService:
    """MemorySearchService tests."""

    def test_search_returns_relevant_results(self, db_session):
        episodic = MemoryServiceFactory(db_session).episodic
        semantic = MemoryServiceFactory(db_session).semantic

        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Python debugging session"))
        semantic.create(
            user_id=1, data=SemanticMemoryCreate(content="Python is a programming language", category="fact")
        )

        search = MemoryServiceFactory(db_session).search
        results = search.search(user_id=1, query="Python")

        assert len(results) == 2
        assert all(r["type"] in ["episodic", "semantic"] for r in results)

    def test_search_scoring_ranks_by_relevance(self, db_session):
        episodic = MemoryServiceFactory(db_session).episodic

        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Critical Python bug fix", importance=0.9))
        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Python code formatting", importance=0.2))

        search = MemoryServiceFactory(db_session).search
        results = search.search(user_id=1, query="Python")

        assert len(results) == 2
        assert results[0]["importance"] >= results[1]["importance"]

    def test_search_type_filter(self, db_session):
        episodic = MemoryServiceFactory(db_session).episodic
        semantic = MemoryServiceFactory(db_session).semantic

        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Python session"))
        semantic.create(user_id=1, data=SemanticMemoryCreate(content="Python fact"))

        search = MemoryServiceFactory(db_session).search

        epi_results = search.search(user_id=1, query="Python", memory_type="episodic")
        assert all(r["type"] == "episodic" for r in epi_results)

        sem_results = search.search(user_id=1, query="Python", memory_type="semantic")
        assert all(r["type"] == "semantic" for r in sem_results)

    def test_search_user_isolation(self, db_session):
        episodic = MemoryServiceFactory(db_session).episodic
        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="User 1 memory"))
        episodic.create(user_id=2, data=EpisodicMemoryCreate(content="User 2 memory"))

        search = MemoryServiceFactory(db_session).search
        results = search.search(user_id=1, query="memory")
        assert len(results) == 1

    def test_search_min_score_threshold(self, db_session):
        episodic = MemoryServiceFactory(db_session).episodic
        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Low relevance content", importance=0.1))

        search = MemoryServiceFactory(db_session).search
        results = search.search(user_id=1, query="Python", min_score=0.5)
        assert len(results) == 0

    def test_search_by_importance(self, db_session):
        episodic = MemoryServiceFactory(db_session).episodic
        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Critical", importance=0.9))
        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Minor", importance=0.2))

        search = MemoryServiceFactory(db_session).search
        results = search.search_by_importance(1, min_importance=0.5)
        assert len(results) == 1
        assert results[0]["importance"] == 0.9

    def test_get_related_memories(self, db_session):
        # Create memories and graph connections
        factory = MemoryServiceFactory(db_session)
        m1 = factory.episodic.create(1, EpisodicMemoryCreate(content="Memory A"))
        m2 = factory.semantic.create(1, SemanticMemoryCreate(content="Memory B"))

        n1 = factory.graph.add_node(1, "episodic", m1.id, "A")
        n2 = factory.graph.add_node(1, "semantic", m2.id, "B")
        factory.graph.add_edge(n1.id, n2.id, "related_to", 0.8)

        results = factory.search.get_related_memories(1, "episodic", m1.id)
        assert len(results) == 1
        assert results[0]["memory_type"] == "semantic"
        assert abs(results[0]["edge_weight"] - 0.8) < 1e-9


# ── Forgetting ────────────────────────────────────────────────


class TestForgettingService:
    """ForgettingService tests."""

    def test_decay_reduces_confidence(self, db_session):
        episodic = MemoryServiceFactory(db_session).episodic
        memory = episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Old memory", importance=0.5))

        # Simulate old memory
        from backend.app.models.memory.episodic import EpisodicMemory

        old_mem = db_session.query(EpisodicMemory).filter(EpisodicMemory.id == memory.id).first()
        old_mem.last_accessed = datetime.utcnow() - timedelta(days=30)
        db_session.commit()

        forgetting = MemoryServiceFactory(db_session).forgetting
        result = forgetting.apply_decay(user_id=1)

        assert result["episodic_decayed"] >= 1

        db_session.refresh(old_mem)
        assert old_mem.confidence < 0.5

    def test_importance_dampens_decay(self, db_session):
        episodic = MemoryServiceFactory(db_session).episodic
        high = episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Important", importance=0.9))
        low = episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Unimportant", importance=0.1))

        from backend.app.models.memory.episodic import EpisodicMemory

        for mem_id in [high.id, low.id]:
            mem = db_session.query(EpisodicMemory).filter(EpisodicMemory.id == mem_id).first()
            mem.last_accessed = datetime.utcnow() - timedelta(days=30)
        db_session.commit()

        forgetting = MemoryServiceFactory(db_session).forgetting
        forgetting.apply_decay(user_id=1)

        high_mem = db_session.query(EpisodicMemory).filter(EpisodicMemory.id == high.id).first()
        low_mem = db_session.query(EpisodicMemory).filter(EpisodicMemory.id == low.id).first()
        assert high_mem.confidence > low_mem.confidence

    def test_garbage_collection_removes_low_confidence(self, db_session):
        episodic = MemoryServiceFactory(db_session).episodic
        memory = episodic.create(user_id=1, data=EpisodicMemoryCreate(content="Very old", importance=0.1))

        from backend.app.models.memory.episodic import EpisodicMemory

        mem = db_session.query(EpisodicMemory).filter(EpisodicMemory.id == memory.id).first()
        mem.confidence = 0.05  # Below GC_THRESHOLD
        db_session.commit()

        forgetting = MemoryServiceFactory(db_session).forgetting
        result = forgetting.apply_decay(user_id=1)

        assert result["episodic_gc"] >= 1
        remaining = db_session.query(EpisodicMemory).filter(EpisodicMemory.id == memory.id).first()
        assert remaining is None

    def test_get_forgetting_stats(self, db_session):
        episodic = MemoryServiceFactory(db_session).episodic
        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="A"))
        episodic.create(user_id=1, data=EpisodicMemoryCreate(content="B"))

        forgetting = MemoryServiceFactory(db_session).forgetting
        stats = forgetting.get_forgetting_stats(1)
        assert stats["total_episodic"] == 2
        assert "avg_episodic_confidence" in stats
