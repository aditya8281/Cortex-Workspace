"""Tests for EngineRegistry and @register decorator."""

from backend.app.agents.integrity.engines._base import Capability, IntegrityEngine
from backend.app.agents.integrity.model.context import ExecutionProfile, IntegrityDomain
from backend.app.agents.integrity.registry import EngineRegistry, register


def test_register_decorator():
    EngineRegistry.get_instance()._engines.clear()

    @register(
        name="test-engine",
        domain=IntegrityDomain.STRUCTURAL,
        capabilities={Capability.IMPORT},
    )
    class TestEngine(IntegrityEngine):
        def analyze(self, model, query, views, context):
            return []

    registry = EngineRegistry.get_instance()
    engine = registry.get("test-engine")
    assert engine is not None
    assert engine["name"] == "test-engine"
    assert engine["domain"] == IntegrityDomain.STRUCTURAL
    assert Capability.IMPORT in engine["capabilities"]


def test_registry_for_profile():
    registry = EngineRegistry.get_instance()
    engines = registry.for_profile(ExecutionProfile.FULL)
    assert isinstance(engines, list)


def test_registry_resolve_order():
    EngineRegistry.get_instance()._engines.clear()

    @register(
        name="dep-engine",
        domain=IntegrityDomain.STRUCTURAL,
        capabilities={Capability.DEPENDENCY},
        required_dependencies=["base-engine"],
    )
    class DepEngine(IntegrityEngine):
        def analyze(self, model, query, views, context):
            return []

    registry = EngineRegistry.get_instance()
    order = registry.resolve_execution_order({ExecutionProfile.FULL})
    assert isinstance(order, list)


def test_capability_values():
    assert Capability.SCHEMA.value == "schema"
    assert Capability.METRICS.value == "metrics"


def test_engine_registry_singleton():
    r1 = EngineRegistry.get_instance()
    r2 = EngineRegistry.get_instance()
    assert r1 is r2
