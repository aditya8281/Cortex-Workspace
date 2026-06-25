"""Tests for ConfigurationEngine."""

from backend.app.agents.integrity.engines.structural.configuration_engine import (
    ConfigurationEngine,
)
from backend.app.agents.integrity.registry import EngineRegistry


def test_configuration_engine_registered():
    reg = EngineRegistry.get_instance()
    assert reg.get("configuration") is not None


def test_configuration_engine_analyze():
    engine = ConfigurationEngine()
    result = engine.analyze(None, None, None, None)
    assert isinstance(result, list)
