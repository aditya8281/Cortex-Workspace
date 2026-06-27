"""Unit tests for EmbeddingService (mock fallback)."""

import pytest

from backend.app.services.intelligence.embedding_service import EMBEDDING_DIM, EmbeddingService


@pytest.fixture(name="svc")
def fixture_svc() -> EmbeddingService:
    return EmbeddingService()


class TestEmbeddingService:
    def test_init(self, svc: EmbeddingService) -> None:
        assert svc.model_path is None or svc.model_path == ""
        assert svc._model is None
        assert svc._tokenizer is None

    def test_embed_single(self, svc: EmbeddingService) -> None:
        vec = svc.embed("hello world")
        assert isinstance(vec, list)
        assert len(vec) == EMBEDDING_DIM
        assert all(isinstance(v, float) for v in vec)

    def test_embed_batch(self, svc: EmbeddingService) -> None:
        results = svc.embed_batch(["hello", "world", "foo bar"])
        assert len(results) == 3
        for vec in results:
            assert len(vec) == EMBEDDING_DIM
            assert all(isinstance(v, float) for v in vec)

    def test_embed_empty_string(self, svc: EmbeddingService) -> None:
        vec = svc.embed("")
        assert isinstance(vec, list)
        assert len(vec) == EMBEDDING_DIM
        assert all(isinstance(v, float) for v in vec)

    def test_model_dimension(self, svc: EmbeddingService) -> None:
        vec = svc.embed("verify dimension")
        assert len(vec) == 768

    def test_mock_fallback(self, svc: EmbeddingService) -> None:
        vec = svc.embed("mock test")
        assert svc._model is None
        assert len(vec) == EMBEDDING_DIM

    def test_embed_reproducible(self, svc: EmbeddingService) -> None:
        v1 = svc.embed("deterministic")
        v2 = svc.embed("deterministic")
        assert v1 == v2

    def test_embed_different_texts_different_vectors(self, svc: EmbeddingService) -> None:
        v1 = svc.embed("cat")
        v2 = svc.embed("dog")
        assert v1 != v2

    def test_embed_batch_single(self, svc: EmbeddingService) -> None:
        results = svc.embed_batch(["only one"])
        assert len(results) == 1
        assert len(results[0]) == EMBEDDING_DIM

    def test_embed_batch_empty(self, svc: EmbeddingService) -> None:
        results = svc.embed_batch([])
        assert results == []

    def test_embed_normalized(self, svc: EmbeddingService) -> None:
        vec = svc.embed("check norm")
        norm = sum(v * v for v in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-6

    def test_without_default_model_loads_nothing(self) -> None:
        svc = EmbeddingService()
        assert svc is not None
        assert svc._model is None

    def test_embed_call_twice(self, svc: EmbeddingService) -> None:
        svc.embed("first")
        svc.embed("second")
        assert svc._model is None
