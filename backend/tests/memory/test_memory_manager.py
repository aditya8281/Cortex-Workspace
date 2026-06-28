"""Tests for MemoryManager service."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from backend.app.services.memory.manager import DEFAULT_COLLECTION, MemoryManager


@pytest.fixture
def db():
    return Mock(spec=["add", "commit", "refresh", "query", "delete", "flush"])


@pytest.fixture
def vector_db():
    return Mock(spec=["upsert", "search", "delete", "list_collections"])


@pytest.fixture
def embedder():
    return Mock(spec=["embed_single", "compute_embedding_id", "embed_batch"])


@pytest.fixture
def manager(db, vector_db, embedder):
    return MemoryManager(db=db, vector_db=vector_db, embedding_service=embedder)


class TestMemoryManager:
    def test_create_memory(self, db, vector_db, embedder, manager):
        """Test creating a memory entry with vector embedding."""
        embedder.compute_embedding_id.return_value = "emb-id-1"
        embedder.embed_single.return_value = [0.1, 0.2, 0.3]

        entry = Mock(spec=["id"])
        entry.id = 42
        db.refresh.side_effect = lambda e: setattr(e, "id", 42)

        manager.create(
            user_id=1,
            title="Test Title",
            content="Test content",
            category="note",
            tags=["tag1", "tag2"],
        )

        embedder.compute_embedding_id.assert_called_once_with("Test Title\nTest content")
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        embedder.embed_single.assert_called_once_with("Test content")
        vector_db.upsert.assert_called_once()

    def test_get_memory(self, db, manager):
        """Test getting a memory entry by ID."""
        expected = Mock(spec=["id", "title", "content"])
        db.query.return_value.filter.return_value.first.return_value = expected

        result = manager.get(1)
        assert result == expected

    def test_get_memory_not_found(self, db, manager):
        """Test getting non-existent memory entry."""
        db.query.return_value.filter.return_value.first.return_value = None

        result = manager.get(999)
        assert result is None

    def test_list_memory(self, db, manager):
        """Test listing memory entries."""
        entry_a = Mock(id=1)
        entry_b = Mock(id=2)

        first_call = True

        def query_side_effect(model):
            nonlocal first_call
            q = Mock()
            q.count.return_value = 2
            q.all.return_value = [entry_a, entry_b]
            q.offset.return_value = q
            q.limit.return_value = q
            q.order_by.return_value = q
            q.filter.return_value = q

            if first_call:
                first_call = False
                q.count.return_value = 2
                q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
                    entry_a,
                    entry_b,
                ]
            else:
                q.with_entities.return_value.group_by.return_value.all.return_value = [
                    ("note", 1),
                    ("code", 1),
                ]
            return q

        db.query.side_effect = query_side_effect

        with patch.object(manager, "_db", db):
            entries, total, categories = manager.list_entries(limit=10, offset=0)

        assert total == 2
        assert len(entries) == 2
        assert categories == {"note": 1, "code": 1}

    def test_search_memory(self, db, vector_db, embedder, manager):
        """Test semantic search."""
        embedder.embed_single.return_value = [0.1, 0.2, 0.3]
        vector_db.search.return_value = [
            {
                "id": "1",
                "score": 0.95,
                "payload": {"entry_id": 1, "user_id": 1, "category": "note"},
            }
        ]

        entry_mock = Mock(
            id=1,
            user_id=1,
            title="Result Title",
            content="Result content",
            category="note",
            source_path=None,
            tags='["a", "b"]',
            embedding_id="emb-1",
            created_at=None,
            updated_at=None,
        )
        db.query.return_value.filter.return_value.all.return_value = [entry_mock]

        results = manager.search("test query", user_id=1, limit=5)

        embedder.embed_single.assert_called_once_with("test query")
        vector_db.search.assert_called_once_with(
            DEFAULT_COLLECTION, [0.1, 0.2, 0.3], limit=5, filter_payload={"user_id": 1}
        )
        assert len(results) == 1
        assert results[0]["score"] == 0.95
        assert results[0]["entry"]["title"] == "Result Title"

    def test_update_memory(self, db, vector_db, embedder, manager):
        """Test updating with content change triggers re-embedding."""
        existing = Mock(
            id=1,
            user_id=1,
            title="Old Title",
            content="Old content",
            category="note",
            tags="[]",
            embedding_id="old-emb",
        )
        db.query.return_value.filter.return_value.first.return_value = existing

        embedder.compute_embedding_id.return_value = "new-emb"
        embedder.embed_single.return_value = [0.7, 0.8, 0.9]

        result = manager.update(1, title="New Title", content="New content")

        assert result is not None
        assert existing.title == "New Title"
        embedder.compute_embedding_id.assert_called_once_with("New Title\nNew content")
        embedder.embed_single.assert_called_once_with("New content")

    def test_delete_memory(self, db, vector_db, manager):
        """Test deleting a memory entry."""
        existing = Mock(id=1, embedding_id="emb-to-delete")
        db.query.return_value.filter.return_value.first.return_value = existing

        result = manager.delete(1)

        assert result is True
        vector_db.delete.assert_called_once_with(DEFAULT_COLLECTION, ["emb-to-delete"])
        db.delete.assert_called_once_with(existing)
        db.commit.assert_called_once()

    def test_serialize_with_tags(self, manager):
        """Test serialization with tags."""
        entry = Mock(
            id=1,
            user_id=1,
            title="Title",
            content="Content",
            category="note",
            source_path="/path",
            tags='["a", "b", "c"]',
            embedding_id="emb-id",
            created_at=None,
            updated_at=None,
        )

        result = manager._serialize(entry)
        assert result["tags"] == ["a", "b", "c"]
        assert result["source_path"] == "/path"

    def test_serialize_no_tags(self, manager):
        """Test serialization with no tags."""
        entry = Mock(
            id=1,
            user_id=1,
            title="Title",
            content="Content",
            category="note",
            source_path=None,
            tags=None,
            embedding_id=None,
            created_at=None,
            updated_at=None,
        )

        result = manager._serialize(entry)
        assert result["tags"] == []
        assert result["source_path"] is None
