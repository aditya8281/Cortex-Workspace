"""Tests for catalogue manager."""

from backend.app.services.catalogue import CatalogueManager, CURATED_FAMILIES


def test_seed_curated_models(_db_session):
    cm = CatalogueManager(_db_session)
    count = cm.seed_curated_models()
    assert count > 0
    assert count == len(CURATED_FAMILIES)


def test_seed_is_idempotent(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    count2 = cm.seed_curated_models()
    assert count2 == 0  # Should not add duplicates


def test_get_all_catalogue(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    models = cm.get_all_catalogue()
    assert len(models) == len(CURATED_FAMILIES)
