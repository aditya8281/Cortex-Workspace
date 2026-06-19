"""Conftest for backend/tests — loads root fixtures and patches external services."""
from unittest.mock import MagicMock, patch

import pytest

pytest_plugins = ["tests.conftest"]


@pytest.fixture(autouse=True)
def _mock_external_services():
    """Mock vector DB and embedding service for all backend integration tests."""
    mock_vector_db = MagicMock()
    mock_vector_db.collection_exists.return_value = True
    mock_vector_db.upsert.return_value = None
    mock_vector_db.search.return_value = []
    mock_vector_db.delete.return_value = None
    mock_vector_db.list_collections.return_value = []

    mock_embedder = MagicMock()
    mock_embedder.embed_single.return_value = [0.1] * 768
    mock_embedder.compute_embedding_id.return_value = "test-embedding-id"

    with (
        patch("backend.app.services.memory_manager.get_vector_db", return_value=mock_vector_db),
        patch("backend.app.services.memory_manager.get_embedding_service", return_value=mock_embedder),
    ):
        yield
