"""Tests for agent relationship integrity — entity linking and graph consistency."""

import uuid

from backend.app.agents.integrity.model.relationship_model import (
    EdgeStrength,
    Multiplicity,
    Relationship,
    RelationshipDirection,
    RelationshipModel,
    RelationshipType,
)


def test_relationship_type_count():
    assert len(RelationshipType) >= 18


def test_relationship_direction_values():
    assert RelationshipDirection.DIRECTED.value == "directed"
    assert RelationshipDirection.BIDIRECTIONAL.value == "bidirectional"


def test_multiplicity_values():
    assert Multiplicity.ONE_TO_ONE.value == "1:1"
    assert Multiplicity.MANY_TO_MANY.value == "N:N"


def test_edge_strength_values():
    assert EdgeStrength.STRONG.value == "strong"
    assert EdgeStrength.WEAK.value == "weak"


def test_relationship_creation():
    source = uuid.uuid4()
    target = uuid.uuid4()
    rel = Relationship(
        type=RelationshipType.IMPORTS,
        direction=RelationshipDirection.DIRECTED,
        multiplicity=Multiplicity.ONE_TO_MANY,
        strength=EdgeStrength.STRONG,
        source_id=source,
        target_id=target,
        source_collector="test",
    )
    assert rel.type == RelationshipType.IMPORTS
    assert rel.source_id == source
    assert rel.target_id == target
    assert isinstance(rel.id, uuid.UUID)


def test_relationship_metadata():
    rel = Relationship(
        type=RelationshipType.CALLS,
        direction=RelationshipDirection.DIRECTED,
        multiplicity=Multiplicity.ONE_TO_ONE,
        strength=EdgeStrength.MEDIUM,
        source_id=uuid.uuid4(),
        target_id=uuid.uuid4(),
        metadata={"line": "42", "file": "app.py"},
        source_collector="test",
    )
    assert rel.metadata["line"] == "42"


def test_relationship_model():
    model = RelationshipModel(edges=[], relationship_schema_version="1.0")
    assert model.relationship_schema_version == "1.0"
    assert len(model.edges) == 0
