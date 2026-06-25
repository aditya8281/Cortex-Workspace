"""Tests for PlanningEngine."""

from backend.app.agents.integrity.engines.evolution.planning_engine import (
    PlanningEngine,
)
from backend.app.agents.integrity.registry import EngineRegistry


def test_planning_engine_registered():
    reg = EngineRegistry.get_instance()
    assert reg.get("planning") is not None


def test_planning_engine_dependency():
    reg = EngineRegistry.get_instance()
    engine = reg.get("planning")
    assert engine is not None
    assert "documentation" in engine["required_dependencies"]
