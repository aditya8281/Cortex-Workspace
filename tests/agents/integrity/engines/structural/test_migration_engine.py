"""Tests for MigrationEngine."""

from backend.app.agents.integrity.engines.structural.migration_engine import (
    MigrationEngine,
)
from backend.app.agents.integrity.registry import EngineRegistry


def test_migration_engine_registered():
    reg = EngineRegistry.get_instance()
    assert reg.get("migration") is not None


def test_migration_engine_analyze():
    engine = MigrationEngine()
    result = engine.analyze(None, None, None, None)
    assert isinstance(result, list)
