"""Tests for DependencyEngine."""

from backend.app.agents.integrity.engines.structural.dependency_engine import (
    DependencyEngine,
)
from backend.app.agents.integrity.registry import EngineRegistry


def test_dependency_engine_registered():
    reg = EngineRegistry.get_instance()
    assert reg.get("dependency") is not None


def test_dependency_engine_analyze():
    engine = DependencyEngine()
    result = engine.analyze(None, None, None, None)
    assert isinstance(result, list)
