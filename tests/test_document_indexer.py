"""Tests for DocumentIndexer."""

import os
import tempfile

import pytest
from sqlalchemy.orm import Session

from backend.app.models.document import Document, DocumentType
from backend.app.services.memory.document_indexer import DocumentIndexer, _detect_doc_type, _file_hash


@pytest.fixture()
def indexer(db_session: Session):
    mock_embedder = type(
        "MockEmbedder",
        (),
        {
            "embed_batch": lambda self, texts: [[0.1] * 768 for _ in texts],
            "embed_single": lambda self, text: [0.1] * 768,
            "compute_embedding_id": lambda self, text: "test_id_" + text[:8],
        },
    )()
    mock_vdb = type(
        "MockVDB",
        (),
        {
            "upsert": lambda self, coll, pts: None,
            "delete": lambda self, coll, ids: None,
        },
    )()
    mock_cache = type(
        "MockCache",
        (),
        {
            "get": lambda self, h, model_name: None,
            "put": lambda self, **kw: None,
        },
    )()
    return DocumentIndexer(db_session, embedding_service=mock_embedder, embedding_cache=mock_cache, vector_db=mock_vdb)


def test_detect_doc_type():
    assert _detect_doc_type("readme.md") == DocumentType.MARKDOWN
    assert _detect_doc_type("notebook.ipynb") == DocumentType.NOTEBOOK
    assert _detect_doc_type("data.txt") == DocumentType.TEXT
    assert _detect_doc_type("script.py") == DocumentType.CODE


def test_file_hash():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("hello world")
        f.flush()
        h = _file_hash(f.name)
    os.unlink(f.name)
    assert len(h) == 32


def test_index_file_markdown(indexer):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Title\n\nSome content here.\n\n## Section\n\nMore content.")
        f.flush()
        result = indexer.index_file(f.name)
    os.unlink(f.name)

    assert result is True
    doc = indexer._db.query(Document).first()
    assert doc is not None
    assert doc.doc_type == DocumentType.MARKDOWN
    assert doc.version == 1


def test_index_file_skip_unchanged(indexer):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Same content")
        f.flush()
        indexer.index_file(f.name)
        result = indexer.index_file(f.name)
    os.unlink(f.name)
    assert result is False


def test_index_file_force_reindex(indexer):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Content")
        f.flush()
        indexer.index_file(f.name)
        result = indexer.index_file(f.name, force=True)
    os.unlink(f.name)
    assert result is True


def test_index_file_nonexistent(indexer):
    assert indexer.index_file("/nonexistent/file.md") is False


def test_remove_file(indexer):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# To be removed")
        f.flush()
        indexer.index_file(f.name)
        result = indexer.remove_file(f.name)
    os.unlink(f.name)
    assert result is True
    assert indexer._db.query(Document).count() == 0


def test_remove_file_nonexistent(indexer):
    assert indexer.remove_file("/nonexistent.md") is False


def test_index_directory(indexer):
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(3):
            with open(os.path.join(tmpdir, f"doc{i}.md"), "w") as f:
                f.write(f"# Doc {i}\n\nContent for doc {i}.")
        stats = indexer.index_directory(tmpdir)
    assert stats["files_indexed"] == 3
    assert stats["errors"] == 0
