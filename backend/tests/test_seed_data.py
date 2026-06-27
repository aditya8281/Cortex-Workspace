"""Tests for seed data service."""

from backend.app.models.model_catalog import Capability, Provider, Quantization
from backend.app.services.system.seed_data import (
    CAPABILITIES,
    PROVIDERS,
    QUANTIZATIONS,
    seed_all,
    seed_capabilities,
    seed_providers,
    seed_quantizations,
)


def test_seed_providers(_db_session):
    count = seed_providers(_db_session)
    assert count == len(PROVIDERS)
    rows = _db_session.execute(_db_session.query(Provider).statement).scalars().all()
    assert len(rows) == len(PROVIDERS)


def test_seed_providers_is_idempotent(_db_session):
    seed_providers(_db_session)
    count2 = seed_providers(_db_session)
    assert count2 == 0


def test_seed_quantizations(_db_session):
    count = seed_quantizations(_db_session)
    assert count == len(QUANTIZATIONS)
    rows = _db_session.execute(_db_session.query(Quantization).statement).scalars().all()
    assert len(rows) == len(QUANTIZATIONS)


def test_seed_quantizations_is_idempotent(_db_session):
    seed_quantizations(_db_session)
    count2 = seed_quantizations(_db_session)
    assert count2 == 0


def test_seed_capabilities(_db_session):
    count = seed_capabilities(_db_session)
    assert count == len(CAPABILITIES)
    rows = _db_session.execute(_db_session.query(Capability).statement).scalars().all()
    assert len(rows) == len(CAPABILITIES)


def test_seed_capabilities_is_idempotent(_db_session):
    seed_capabilities(_db_session)
    count2 = seed_capabilities(_db_session)
    assert count2 == 0


def test_seed_all(_db_session):
    result = seed_all(_db_session)
    assert result["providers"] == len(PROVIDERS)
    assert result["quantizations"] == len(QUANTIZATIONS)
    assert result["capabilities"] == len(CAPABILITIES)


def test_seed_all_is_idempotent(_db_session):
    seed_all(_db_session)
    result2 = seed_all(_db_session)
    assert result2["providers"] == 0
    assert result2["quantizations"] == 0
    assert result2["capabilities"] == 0


def test_provider_names_unique(_db_session):
    names = [p["name"] for p in PROVIDERS]
    assert len(names) == len(set(names))


def test_quantization_names_unique(_db_session):
    names = [q["name"] for q in QUANTIZATIONS]
    assert len(names) == len(set(names))


def test_capability_names_unique(_db_session):
    names = [c["name"] for c in CAPABILITIES]
    assert len(names) == len(set(names))
