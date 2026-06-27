"""Tests for v1.03 P01 — memory models and schemas."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from backend.app.models.memory.episodic import EpisodicMemory
from backend.app.models.memory.memory_graph import MemoryEdge, MemoryNode
from backend.app.models.memory.semantic import SemanticMemory
from backend.app.models.memory.working import WorkingMemory
from backend.app.schemas.memory.episodic import (
    EpisodicMemoryCreate,
    EpisodicMemoryResponse,
    EpisodicMemoryUpdate,
)
from backend.app.schemas.memory.graph import MemoryEdgeCreate, MemoryNodeCreate
from backend.app.schemas.memory.semantic import SemanticMemoryCreate, SemanticMemoryUpdate
from backend.app.schemas.memory.working import WorkingMemoryCreate, WorkingMemoryUpdate


class TestEpisodicMemoryModel:
    """Episodic memory model tests."""

    def test_creation(self, db_session):
        memory = EpisodicMemory(
            user_id=1, content="Test experience", importance=0.8, context={"source": "chat"}, emotion="excited"
        )
        db_session.add(memory)
        db_session.commit()
        assert memory.id is not None
        assert memory.content == "Test experience"
        assert memory.importance == 0.8
        assert memory.confidence == 0.5
        assert memory.access_count == 0
        assert memory.recency_score == 1.0

    def test_defaults(self, db_session):
        memory = EpisodicMemory(user_id=1, content="Minimal memory")
        db_session.add(memory)
        db_session.commit()
        assert memory.importance == 0.5
        assert memory.confidence == 0.5
        assert memory.access_count == 0
        assert memory.recency_score == 1.0
        assert memory.context is None
        assert memory.emotion is None
        assert memory.expires_at is None

    def test_user_isolation(self, db_session):
        m1 = EpisodicMemory(user_id=1, content="User 1 memory")
        m2 = EpisodicMemory(user_id=2, content="User 2 memory")
        db_session.add_all([m1, m2])
        db_session.commit()
        results = db_session.query(EpisodicMemory).filter(EpisodicMemory.user_id == 1).all()
        assert len(results) == 1
        assert results[0].content == "User 1 memory"

    def test_json_context(self, db_session):
        ctx = {"source": "chat", "trigger": "question", "env": "terminal"}
        memory = EpisodicMemory(user_id=1, content="Context test", context=ctx)
        db_session.add(memory)
        db_session.commit()
        assert memory.context == ctx


class TestSemanticMemoryModel:
    """Semantic memory model tests."""

    def test_creation(self, db_session):
        memory = SemanticMemory(user_id=1, content="Python is a language", category="fact", source="user_input")
        db_session.add(memory)
        db_session.commit()
        assert memory.id is not None
        assert memory.category == "fact"
        assert memory.source == "user_input"
        assert memory.confidence == 0.5

    def test_defaults(self, db_session):
        memory = SemanticMemory(user_id=1, content="Minimal semantic")
        db_session.add(memory)
        db_session.commit()
        assert memory.confidence == 0.5
        assert memory.access_count == 0
        assert memory.category is None
        assert memory.source is None

    def test_user_isolation(self, db_session):
        m1 = SemanticMemory(user_id=1, content="User 1 fact")
        m2 = SemanticMemory(user_id=2, content="User 2 fact")
        db_session.add_all([m1, m2])
        db_session.commit()
        results = db_session.query(SemanticMemory).filter(SemanticMemory.user_id == 1).all()
        assert len(results) == 1


class TestWorkingMemoryModel:
    """Working memory model tests."""

    def test_creation(self, db_session):
        memory = WorkingMemory(
            user_id=1,
            session_id="test-session-uuid",
            content="Current task",
            slot="active",
            priority=5,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(memory)
        db_session.commit()
        assert memory.id is not None
        assert memory.slot == "active"
        assert memory.session_id == "test-session-uuid"
        assert memory.expires_at is not None

    def test_session_isolation(self, db_session):
        now = datetime.utcnow() + timedelta(hours=1)
        m1 = WorkingMemory(user_id=1, session_id="session-a", content="A", expires_at=now)
        m2 = WorkingMemory(user_id=1, session_id="session-b", content="B", expires_at=now)
        db_session.add_all([m1, m2])
        db_session.commit()
        results = (
            db_session.query(WorkingMemory)
            .filter(WorkingMemory.user_id == 1, WorkingMemory.session_id == "session-a")
            .all()
        )
        assert len(results) == 1

    def test_slot_values(self, db_session):
        now = datetime.utcnow() + timedelta(hours=1)
        for slot in ("active", "buffer", "archive"):
            memory = WorkingMemory(
                user_id=1, session_id=f"sess-{slot}", content=f"Item {slot}", slot=slot, expires_at=now
            )
            db_session.add(memory)
        db_session.commit()
        results = db_session.query(WorkingMemory).filter(WorkingMemory.user_id == 1).all()
        assert len(results) == 3


class TestMemoryNodeModel:
    """Memory graph node tests."""

    def test_creation(self, db_session):
        node = MemoryNode(user_id=1, memory_type="episodic", memory_id=1, label="Test node")
        db_session.add(node)
        db_session.commit()
        assert node.id is not None
        assert node.memory_type == "episodic"

    def test_unique_constraint(self, db_session):
        n1 = MemoryNode(user_id=1, memory_type="episodic", memory_id=1, label="N1")
        n2 = MemoryNode(user_id=1, memory_type="episodic", memory_id=1, label="N2")
        db_session.add_all([n1, n2])
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestMemoryEdgeModel:
    """Memory graph edge tests."""

    def test_creation(self, db_session):
        n1 = MemoryNode(user_id=1, memory_type="episodic", memory_id=1, label="N1")
        n2 = MemoryNode(user_id=1, memory_type="semantic", memory_id=1, label="N2")
        db_session.add_all([n1, n2])
        db_session.commit()

        edge = MemoryEdge(source_id=n1.id, target_id=n2.id, edge_type="related_to", weight=0.7)
        db_session.add(edge)
        db_session.commit()
        assert edge.id is not None
        assert edge.weight == 0.7
        assert edge.edge_type == "related_to"


class TestEpisodicSchemaValidation:
    """Episodic memory Pydantic schema tests."""

    def test_create_valid(self):
        schema = EpisodicMemoryCreate(content="Test", importance=0.8)
        assert schema.content == "Test"
        assert schema.importance == 0.8

    def test_create_invalid_importance(self):
        with pytest.raises(ValidationError):
            EpisodicMemoryCreate(content="Test", importance=1.5)

    def test_create_empty_content(self):
        with pytest.raises(ValidationError):
            EpisodicMemoryCreate(content="")

    def test_create_secret_rejection(self):
        with pytest.raises(ValidationError):
            EpisodicMemoryCreate(content="api_key=sk-1234567890abcdef1234")

    def test_create_password_rejection(self):
        with pytest.raises(ValidationError):
            EpisodicMemoryCreate(content="password=hunter2")

    def test_update_partial(self):
        schema = EpisodicMemoryUpdate(content="Updated")
        assert schema.content == "Updated"
        assert schema.emotion is None

    def test_response_from_attributes(self):
        data = {
            "id": 1,
            "user_id": 1,
            "content": "Test",
            "context": None,
            "emotion": None,
            "importance": 0.5,
            "confidence": 0.5,
            "access_count": 0,
            "last_accessed": None,
            "created_at": datetime.utcnow(),
            "updated_at": None,
            "recency_score": 1.0,
        }
        resp = EpisodicMemoryResponse(**data)
        assert resp.id == 1


class TestSemanticSchemaValidation:
    """Semantic memory Pydantic schema tests."""

    def test_category_normalization(self):
        schema = SemanticMemoryCreate(content="Test", category="  User  Preference  ")
        assert schema.category == "user_preference"

    def test_category_hyphen(self):
        schema = SemanticMemoryCreate(content="Test", category="my-category")
        assert schema.category == "my_category"

    def test_update_category(self):
        schema = SemanticMemoryUpdate(content="Updated", category="FACT")
        assert schema.category == "fact"


class TestWorkingSchemaValidation:
    """Working memory Pydantic schema tests."""

    def test_valid_slot(self):
        schema = WorkingMemoryCreate(session_id="test", content="Test", slot="active")
        assert schema.slot == "active"

    def test_invalid_slot(self):
        with pytest.raises(ValidationError):
            WorkingMemoryCreate(session_id="test", content="Test", slot="invalid")

    def test_update_slot_valid(self):
        schema = WorkingMemoryUpdate(slot="buffer")
        assert schema.slot == "buffer"

    def test_update_slot_invalid(self):
        with pytest.raises(ValidationError):
            WorkingMemoryUpdate(slot="nope")


class TestGraphSchemaValidation:
    """Graph node/edge Pydantic schema tests."""

    def test_node_valid_type(self):
        schema = MemoryNodeCreate(memory_type="episodic", memory_id=1, label="Test")
        assert schema.memory_type == "episodic"

    def test_node_invalid_type(self):
        with pytest.raises(ValidationError):
            MemoryNodeCreate(memory_type="invalid", memory_id=1, label="Test")

    def test_edge_creation(self):
        schema = MemoryEdgeCreate(source_id=1, target_id=2, edge_type="related_to", weight=0.7)
        assert schema.weight == 0.7
        assert schema.edge_type == "related_to"

    def test_edge_invalid_weight(self):
        with pytest.raises(ValidationError):
            MemoryEdgeCreate(source_id=1, target_id=2, edge_type="test", weight=1.5)
