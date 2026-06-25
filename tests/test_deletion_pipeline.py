"""Tests for DeletionPipeline."""

import pytest
from sqlalchemy.orm import Session

from backend.app.models.document import Document, DocumentChunk, DocumentType
from backend.app.services.deletion_pipeline import DeletionPipeline


@pytest.fixture()
def pipeline(db_session: Session) -> DeletionPipeline:
    mock_vector_db = type(
        "MockVectorDB",
        (),
        {
            "delete": lambda self, coll, ids: None,
            "collection_exists": lambda self, coll: True,
        },
    )()
    mock_cache = type(
        "MockEmbeddingCache",
        (),
        {
            "invalidate": lambda self, h: 1,
        },
    )()
    return DeletionPipeline(db_session, vector_db=mock_vector_db, embedding_cache=mock_cache)


def _create_doc(db_session: Session, path: str = "/docs/test.md") -> Document:
    doc = Document(
        path=path,
        filename=path.split("/")[-1],
        content_hash="abc123",
        doc_type=DocumentType.MARKDOWN,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    chunk = DocumentChunk(
        document_id=doc.id,
        content="test content",
        chunk_index=0,
        token_count=2,
        embedding_id="emb_test_123",
    )
    db_session.add(chunk)
    db_session.commit()
    return doc


def test_soft_delete(db_session: Session, pipeline: DeletionPipeline):
    doc = _create_doc(db_session)
    assert pipeline.soft_delete(doc.id)

    db_session.refresh(doc)
    assert doc.deleted_at is not None


def test_soft_delete_idempotent(db_session: Session, pipeline: DeletionPipeline):
    doc = _create_doc(db_session)
    pipeline.soft_delete(doc.id)
    assert not pipeline.soft_delete(doc.id)


def test_restore(db_session: Session, pipeline: DeletionPipeline):
    doc = _create_doc(db_session)
    pipeline.soft_delete(doc.id)
    assert pipeline.restore(doc.id)

    db_session.refresh(doc)
    assert doc.deleted_at is None


def test_restore_non_deleted(db_session: Session, pipeline: DeletionPipeline):
    doc = _create_doc(db_session)
    assert not pipeline.restore(doc.id)


def test_hard_delete(db_session: Session, pipeline: DeletionPipeline):
    doc = _create_doc(db_session)
    assert pipeline.hard_delete(doc.id)

    remaining = db_session.query(Document).filter(Document.id == doc.id).first()
    assert remaining is None


def test_hard_delete_cascades(db_session: Session, pipeline: DeletionPipeline):
    doc = _create_doc(db_session)
    pipeline.hard_delete(doc.id)

    chunks = db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    assert len(chunks) == 0


def test_delete_by_path(db_session: Session, pipeline: DeletionPipeline):
    doc = _create_doc(db_session, path="/docs/special.md")
    assert pipeline.delete_by_path("/docs/special.md")

    db_session.refresh(doc)
    assert doc.deleted_at is not None


def test_delete_by_path_nonexistent(db_session: Session, pipeline: DeletionPipeline):
    assert not pipeline.delete_by_path("/nonexistent.md")


def test_cleanup_orphans(db_session: Session, pipeline: DeletionPipeline):
    from datetime import datetime, timedelta, timezone

    doc = _create_doc(db_session, path="/docs/old.md")
    doc.deleted_at = datetime.now(timezone.utc) - timedelta(days=31)
    db_session.commit()

    stats = pipeline.cleanup_orphans()
    assert stats["hard_deleted"] == 1

    remaining = db_session.query(Document).filter(Document.id == doc.id).first()
    assert remaining is None


def test_cleanup_orphans_preserves_recent(db_session: Session, pipeline: DeletionPipeline):
    from datetime import datetime, timedelta, timezone

    doc = _create_doc(db_session, path="/docs/recent.md")
    doc.deleted_at = datetime.now(timezone.utc) - timedelta(days=5)
    db_session.commit()

    stats = pipeline.cleanup_orphans()
    assert stats["hard_deleted"] == 0
