"""Tests for SchemaEngine."""

from backend.app.agents.integrity.engines.semantic.schema_engine import (
    SchemaEngine,
)
from backend.app.agents.integrity.registry import EngineRegistry


def test_schema_engine_registered():
    reg = EngineRegistry.get_instance()
    assert reg.get("schema-engine") is not None


def test_schema_engine_analyze():
    engine = SchemaEngine()
    result = engine.analyze(None, None, None, None)
    assert isinstance(result, list)
