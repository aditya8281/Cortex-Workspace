"""Conftest for backend/tests — loads root fixtures and patches external services."""

from unittest.mock import MagicMock, patch

import pytest

pytest_plugins = ["tests.conftest"]


@pytest.fixture(autouse=True)
def _mock_external_services():
    """Mock vector DB, embedding service, and cache for all backend integration tests."""
    mock_vector_db = MagicMock()
    mock_vector_db.collection_exists.return_value = True
    mock_vector_db.upsert.return_value = None
    mock_vector_db.search.return_value = []
    mock_vector_db.delete.return_value = None
    mock_vector_db.list_collections.return_value = []

    mock_embedder = MagicMock()
    mock_embedder.embed_single.return_value = [0.1] * 768
    mock_embedder.embed_batch.side_effect = lambda texts: [[0.1] * 768 for _ in texts]
    mock_embedder.compute_embedding_id.return_value = "test-embedding-id"

    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    mock_cache.put.return_value = None
    mock_cache.invalidate.return_value = 0

    mock_file_watcher = MagicMock()
    mock_file_watcher.watch.return_value = True
    mock_file_watcher.unwatch.return_value = True
    mock_file_watcher.start.return_value = None
    mock_file_watcher.stop.return_value = None

    with (
        patch("backend.app.services.memory_manager.get_vector_db", return_value=mock_vector_db),
        patch("backend.app.services.memory_manager.get_embedding_service", return_value=mock_embedder),
        patch("backend.app.services.repo_scanner.get_embedding_service", return_value=mock_embedder),
        patch("backend.app.services.repo_scanner.get_vector_db", return_value=mock_vector_db),
        patch("backend.app.services.embedding_cache.get_embedding_cache", return_value=mock_cache),
        patch("backend.app.services.deletion_pipeline.get_vector_db", return_value=mock_vector_db),
        patch("backend.app.services.deletion_pipeline.get_embedding_cache", return_value=mock_cache),
        patch("backend.app.services.document_indexer.get_vector_db", return_value=mock_vector_db),
        patch("backend.app.services.document_indexer.get_embedding_service", return_value=mock_embedder),
        patch("backend.app.services.document_indexer.get_embedding_cache", return_value=mock_cache),
        patch("backend.app.services.indexing_orchestrator.get_file_watcher_v2", return_value=mock_file_watcher),
    ):
        yield
