"""Tests for model search service."""

from backend.app.services.catalogue import CatalogueManager
from backend.app.services.model_search import ModelSearchService


def test_text_search(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.search("llama")
    assert len(results) > 0


def test_natural_language_search_coding(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.search("best coding model")
    assert len(results) > 0
    assert all("code" in (m.capabilities or []) for m in results)


def test_natural_language_search_vision(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.search("vision model")
    assert len(results) > 0
    assert all("vision" in (m.capabilities or []) for m in results)


def test_natural_language_search_small(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.search("small model")
    assert len(results) > 0
    assert all((m.parameter_count or 0) <= 4.0 for m in results)


def test_natural_language_search_large(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.search("large model")
    assert len(results) > 0
    assert all((m.parameter_count or 0) >= 30.0 for m in results)


def test_filter_by_capability(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.filter(capabilities=["code"])
    assert len(results) > 0
    assert all("code" in (m.capabilities or []) for m in results)


def test_filter_by_provider(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.filter(provider="ollama")
    assert len(results) > 0
    assert all(m.provider == "ollama" for m in results)


def test_filter_by_family(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.filter(family="qwen")
    assert len(results) > 0
    assert all(m.family == "qwen" for m in results)


def test_filter_by_params(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.filter(min_params=8.0, max_params=20.0)
    assert len(results) > 0
    assert all(8.0 <= (m.parameter_count or 0) <= 20.0 for m in results)


def test_sort_by_popularity(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.filter(sort="popularity")
    assert len(results) > 0


def test_sort_by_name(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.filter(sort="name")
    assert len(results) > 0
    names = [m.display_name for m in results]
    assert names == sorted(names)


def test_autocomplete(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    suggestions = svc.autocomplete("ll")
    assert len(suggestions) > 0
    assert all(s.lower().startswith("ll") for s in suggestions)


def test_autocomplete_no_match(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    suggestions = svc.autocomplete("zzzzzzz")
    assert suggestions == []


def test_search_no_results(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.search("zzzzzzz_nonexistent_model")
    assert results == []


def test_filter_limit(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.filter(limit=2)
    assert len(results) <= 2


def test_natural_language_embedding(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.search("embedding")
    assert len(results) > 0
    assert all("embedding" in (m.capabilities or []) for m in results)


def test_natural_language_reasoning(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.search("reasoning")
    assert len(results) > 0
    assert all("reasoning" in (m.capabilities or []) for m in results)


def test_text_search_family(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.search("deepseek")
    assert len(results) > 0
    assert all("deepseek" in (m.family or "").lower() for m in results)


def test_filter_combined(_db_session):
    cm = CatalogueManager(_db_session)
    cm.seed_curated_models()
    svc = ModelSearchService(_db_session)
    results = svc.filter(capabilities=["code"], family="qwen")
    assert len(results) > 0
    assert all(
        "code" in (m.capabilities or []) and m.family == "qwen"
        for m in results
    )
