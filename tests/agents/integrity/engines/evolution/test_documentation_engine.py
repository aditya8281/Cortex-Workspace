"""Tests for DocumentationEngine."""

from backend.app.agents.integrity.engines.evolution.documentation_engine import (
    DocumentationEngine,
)
from backend.app.agents.integrity.registry import EngineRegistry


def test_documentation_engine_registered():
    reg = EngineRegistry.get_instance()
    assert reg.get("documentation") is not None


def test_documentation_engine_analyze():
    engine = DocumentationEngine()
    result = engine.analyze(None, None, None, None)
    assert isinstance(result, list)
