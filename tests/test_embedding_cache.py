"""Tests for EmbeddingCache model and EmbeddingCacheService."""


import pytest
from sqlalchemy.orm import Session

from backend.app.models.embedding_cache import EmbeddingCache
from backend.app.services.embedding_cache import EmbeddingCacheService


@pytest.fixture()
def cache_service(db_session: Session) -> EmbeddingCacheService:
    return EmbeddingCacheService(db_session)


def test_put_and_get(db_session: Session, cache_service: EmbeddingCacheService):
    embedding = [0.1] * 768
    cache_service.put("hash1", embedding, model_name="nomic-embed-text")

    result = cache_service.get("hash1", model_name="nomic-embed-text")
    assert result is not None
    assert len(result) == 768
    assert result[0] == pytest.approx(0.1)


def test_cache_miss(db_session: Session, cache_service: EmbeddingCacheService):
    result = cache_service.get("nonexistent", model_name="nomic-embed-text")
    assert result is None


def test_invalidate(db_session: Session, cache_service: EmbeddingCacheService):
    cache_service.put("hash1", [0.1] * 768, model_name="nomic-embed-text")
    assert cache_service.get("hash1", model_name="nomic-embed-text") is not None

    count = cache_service.invalidate("hash1")
    assert count == 1
    assert cache_service.get("hash1", model_name="nomic-embed-text") is None


def test_invalidate_all(db_session: Session, cache_service: EmbeddingCacheService):
    cache_service.put("h1", [0.1] * 768, model_name="model-a")
    cache_service.put("h2", [0.2] * 768, model_name="model-b")

    count = cache_service.invalidate_all()
    assert count == 2
    assert cache_service.get("h1", model_name="model-a") is None
    assert cache_service.get("h2", model_name="model-b") is None


def test_invalidate_all_by_model(db_session: Session, cache_service: EmbeddingCacheService):
    cache_service.put("h1", [0.1] * 768, model_name="model-a")
    cache_service.put("h2", [0.2] * 768, model_name="model-b")

    count = cache_service.invalidate_all(model_name="model-a")
    assert count == 1
    assert cache_service.get("h1", model_name="model-a") is None
    assert cache_service.get("h2", model_name="model-b") is not None


def test_upsert_on_conflict(db_session: Session, cache_service: EmbeddingCacheService):
    cache_service.put("hash1", [0.1] * 768, model_name="nomic-embed-text")
    cache_service.put("hash1", [0.2] * 768, model_name="nomic-embed-text")

    result = cache_service.get("hash1", model_name="nomic-embed-text")
    assert result is not None
    assert result[0] == pytest.approx(0.2)


def test_stats(db_session: Session, cache_service: EmbeddingCacheService):
    cache_service.put("h1", [0.1] * 768, model_name="m1")
    cache_service.put("h2", [0.2] * 768, model_name="m1")

    stats = cache_service.stats()
    assert stats["total_entries"] == 2


def test_access_count_increments(db_session: Session, cache_service: EmbeddingCacheService):
    cache_service.put("hash1", [0.1] * 768, model_name="m1")
    cache_service.get("hash1", model_name="m1")
    cache_service.get("hash1", model_name="m1")

    entry = db_session.query(EmbeddingCache).filter(EmbeddingCache.content_hash == "hash1").first()
    assert entry.access_count == 3  # 1 put + 2 gets


def test_embed_with_cache(db_session: Session, cache_service: EmbeddingCacheService):
    from backend.app.services.embedding_service import EmbeddingService

    embedder = EmbeddingService.__new__(EmbeddingService)
    embedder._backend = "mock"
    embedder._model = None
    embedder._tokenizer = None
    embedder._load_failed = False
    embedder.model_path = ""

    text = "test embedding with cache"
    result1 = embedder.embed_with_cache(text, cache_service)
    assert len(result1) == 768

    result2 = embedder.embed_with_cache(text, cache_service)
    assert result1 == result2

    stats = cache_service.stats()
    assert stats["total_entries"] == 1
