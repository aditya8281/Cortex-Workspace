"""Tests for agent entity base — core entity types and relationships."""

# tests/agents/integrity/test_entity_base.py
import uuid

from backend.app.agents.integrity.model._base import EntityBase


def test_entity_base_has_uuid():
    class Concrete(EntityBase):
        pass

    e = Concrete(confidence=1.0, source_collector="test", source_version="1.0")
    assert isinstance(e.id, uuid.UUID)


def test_entity_base_confidence_range():
    class Concrete(EntityBase):
        pass

    e = Concrete(confidence=0.5, source_collector="test", source_version="1.0")
    assert e.confidence == 0.5


def test_entity_base_source_fields():
    class Concrete(EntityBase):
        pass

    e = Concrete(confidence=0.8, source_collector="python", source_version="1.0")
    assert e.confidence == 0.8
    assert e.source_collector == "python"
    assert e.source_version == "1.0"
