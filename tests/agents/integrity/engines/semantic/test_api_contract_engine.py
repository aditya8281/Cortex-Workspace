"""Tests for APIContractEngine."""

from backend.app.agents.integrity.registry import EngineRegistry


def test_api_contract_engine_registered():
    reg = EngineRegistry.get_instance()
    assert reg.get("api-contract") is not None


def test_api_contract_engine_dependency():
    reg = EngineRegistry.get_instance()
    engine = reg.get("api-contract")
    assert engine is not None
    assert "schema-engine" in engine["required_dependencies"]
