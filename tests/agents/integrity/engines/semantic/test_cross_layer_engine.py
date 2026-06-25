"""Tests for CrossLayerEngine."""

from backend.app.agents.integrity.engines.semantic.cross_layer_engine import (
    CrossLayerEngine,
)
from backend.app.agents.integrity.registry import EngineRegistry


def test_cross_layer_engine_registered():
    reg = EngineRegistry.get_instance()
    assert reg.get("cross-layer") is not None


def test_cross_layer_engine_analyze():
    engine = CrossLayerEngine()
    result = engine.analyze(None, None, None, None)
    assert isinstance(result, list)
