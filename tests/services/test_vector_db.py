"""Tests for vector DB service — Qdrant operations and embedding storage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from backend.app.core.vector_db import VectorDB


@patch("backend.app.core.vector_db.QdrantClient")
def test_init_defaults(mock_qdrant_cls):
    VectorDB()
    mock_qdrant_cls.assert_called_once_with(host="localhost", port=6333, prefer_grpc=False)


@patch("backend.app.core.vector_db.QdrantClient")
def test_init_custom(mock_qdrant_cls):
    VectorDB(host="10.0.0.1", port=9999)
    mock_qdrant_cls.assert_called_once_with(host="10.0.0.1", port=9999, prefer_grpc=False)


@patch("backend.app.core.vector_db.QdrantClient")
def test_upsert_creates_collection(mock_qdrant_cls):
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False
    mock_qdrant_cls.return_value = mock_client

    db = VectorDB()
    points = [
        {"id": 1, "vector": [0.1, 0.2], "payload": {"text": "hello"}},
        {"id": 2, "vector": [0.3, 0.4], "payload": {"text": "world"}},
    ]
    db.upsert("my_collection", points)

    mock_client.collection_exists.assert_called_once_with("my_collection")
    mock_client.create_collection.assert_called_once()
    _, create_kwargs = mock_client.create_collection.call_args
    assert create_kwargs["collection_name"] == "my_collection"

    mock_client.upsert.assert_called_once()
    _, upsert_kwargs = mock_client.upsert.call_args
    assert upsert_kwargs["collection_name"] == "my_collection"
    assert len(upsert_kwargs["points"]) == 2
    assert upsert_kwargs["points"][0].id == 1
    assert upsert_kwargs["points"][1].id == 2


@patch("backend.app.core.vector_db.QdrantClient")
def test_upsert_existing_collection(mock_qdrant_cls):
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_qdrant_cls.return_value = mock_client

    db = VectorDB()
    db.upsert("existing_collection", [{"id": 1, "vector": [0.1, 0.2]}])

    mock_client.create_collection.assert_not_called()
    mock_client.upsert.assert_called_once()


@patch("backend.app.core.vector_db.QdrantClient")
def test_search(mock_qdrant_cls):
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True

    hit1 = MagicMock()
    hit1.id = 1
    hit1.score = 0.95
    hit1.payload = {"text": "doc1"}
    hit2 = MagicMock()
    hit2.id = 2
    hit2.score = 0.87
    hit2.payload = {"text": "doc2"}
    mock_response = MagicMock()
    mock_response.points = [hit1, hit2]
    mock_client.query_points.return_value = mock_response

    mock_qdrant_cls.return_value = mock_client

    db = VectorDB()
    results = db.search("my_collection", [0.1, 0.2, 0.3], limit=5)

    mock_client.query_points.assert_called_once_with(
        collection_name="my_collection",
        query=[0.1, 0.2, 0.3],
        limit=5,
        query_filter=None,
    )
    assert results == [
        {"id": 1, "score": 0.95, "payload": {"text": "doc1"}},
        {"id": 2, "score": 0.87, "payload": {"text": "doc2"}},
    ]


@patch("backend.app.core.vector_db.QdrantClient")
def test_search_missing_collection(mock_qdrant_cls):
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False
    mock_qdrant_cls.return_value = mock_client

    db = VectorDB()
    results = db.search("nonexistent", [0.1, 0.2, 0.3])

    assert results == []
    mock_client.query_points.assert_not_called()


@patch("backend.app.core.vector_db.QdrantClient")
def test_delete(mock_qdrant_cls):
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_qdrant_cls.return_value = mock_client

    db = VectorDB()
    db.delete("my_collection", ["id1", "id2"])

    mock_client.delete.assert_called_once()
    _, kwargs = mock_client.delete.call_args
    assert kwargs["collection_name"] == "my_collection"


@patch("backend.app.core.vector_db.QdrantClient")
def test_delete_missing_collection(mock_qdrant_cls):
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False
    mock_qdrant_cls.return_value = mock_client

    db = VectorDB()
    db.delete("ghost", ["id1"])

    mock_client.delete.assert_not_called()


@patch("backend.app.core.vector_db.QdrantClient")
def test_list_collections(mock_qdrant_cls):
    mock_client = MagicMock()
    col1 = MagicMock()
    col1.name = "articles"
    col2 = MagicMock()
    col2.name = "embeddings"
    mock_client.get_collections.return_value.collections = [col1, col2]
    mock_qdrant_cls.return_value = mock_client

    db = VectorDB()
    result = db.list_collections()

    assert result == ["articles", "embeddings"]
    mock_client.get_collections.assert_called_once()


@patch("backend.app.core.vector_db.QdrantClient")
def test_list_collections_empty(mock_qdrant_cls):
    mock_client = MagicMock()
    mock_client.get_collections.return_value.collections = []
    mock_qdrant_cls.return_value = mock_client

    db = VectorDB()
    result = db.list_collections()

    assert result == []


@patch("backend.app.core.vector_db.QdrantClient")
def test_health_check(mock_qdrant_cls):
    mock_client = MagicMock()
    mock_client.get_collections.return_value = MagicMock(collections=[])
    mock_qdrant_cls.return_value = mock_client

    db = VectorDB()
    # list_collections() doubles as a connectivity check — if Qdrant is
    # unreachable it will raise, so a successful return proves health.
    assert db.list_collections() == []
    mock_client.get_collections.assert_called_once()
