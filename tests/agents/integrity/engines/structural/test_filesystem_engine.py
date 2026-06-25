"""Tests for FilesystemEngine."""

from backend.app.agents.integrity.engines.structural.filesystem_engine import (
    FilesystemEngine,
)
from backend.app.agents.integrity.registry import EngineRegistry


def test_filesystem_engine_registered():
    reg = EngineRegistry.get_instance()
    assert reg.get("filesystem") is not None


def test_filesystem_engine_analyze():
    engine = FilesystemEngine()
    result = engine.analyze(None, None, None, None)
    assert isinstance(result, list)
