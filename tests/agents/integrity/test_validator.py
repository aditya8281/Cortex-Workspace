"""Tests for Validator."""

import uuid

from backend.app.agents.integrity.model._base import EntityBase
from backend.app.agents.integrity.model.relationship_model import (
    EdgeStrength,
    Multiplicity,
    Relationship,
    RelationshipDirection,
    RelationshipType,
)
from backend.app.agents.integrity.validation import Validator


def test_validate_entity_valid():
    class E(EntityBase):
        pass

    e = E(confidence=0.5, source_collector="test", source_version="1.0")
    v = Validator()
    result = v.validate_entity(e)
    assert result.passed is True
    assert len(result.errors) == 0


def test_validate_entity_confidence_out_of_range():
    class E(EntityBase):
        pass

    e = E(confidence=1.5, source_collector="test", source_version="1.0")
    v = Validator()
    result = v.validate_entity(e)
    assert result.passed is False
    assert any("confidence" in str(err).lower() for err in result.errors)


def test_validate_entity_negative_confidence():
    class E(EntityBase):
        pass

    e = E(confidence=-0.1, source_collector="test", source_version="1.0")
    v = Validator()
    result = v.validate_entity(e)
    assert result.passed is False


def test_validate_relationship_valid():
    rel = Relationship(
        type=RelationshipType.IMPORTS,
        direction=RelationshipDirection.DIRECTED,
        multiplicity=Multiplicity.ONE_TO_MANY,
        strength=EdgeStrength.STRONG,
        source_id=uuid.uuid4(),
        target_id=uuid.uuid4(),
        source_collector="test",
    )
    v = Validator()
    result = v.validate_relationship(rel)
    assert result.passed is True


def test_validate_relationship_self_reference():
    id_ = uuid.uuid4()
    rel = Relationship(
        type=RelationshipType.REFERENCES,
        direction=RelationshipDirection.DIRECTED,
        multiplicity=Multiplicity.ONE_TO_ONE,
        strength=EdgeStrength.WEAK,
        source_id=id_,
        target_id=id_,
        source_collector="test",
    )
    v = Validator()
    result = v.validate_relationship(rel)
    assert result.passed is False


def test_validator_warnings():
    class E(EntityBase):
        pass

    e = E(confidence=1.0, source_collector="test", source_version="1.0")
    v = Validator()
    result = v.validate_entity(e)
    assert isinstance(result.warnings, list)
