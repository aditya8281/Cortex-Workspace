"""Tests for ImportGraphEngine."""

from backend.app.agents.integrity.engines._base import Capability
from backend.app.agents.integrity.engines.structural.import_engine import (
    ImportGraphEngine,
)
from backend.app.agents.integrity.registry import EngineRegistry


def test_import_engine_registered():
    reg = EngineRegistry.get_instance()
    engine = reg.get("import-graph")
    assert engine is not None
    assert Capability.IMPORT in engine["capabilities"]


def test_import_engine_analyze_empty():
    engine = ImportGraphEngine()
    result = engine.analyze(None, None, None, None)
    assert isinstance(result, list)


def test_import_engine_name():
    engine = ImportGraphEngine()
    assert engine.name == "import-graph"
