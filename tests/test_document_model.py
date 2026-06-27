"""Tests for Document and DocumentChunk ORM models."""

from sqlalchemy.orm import Session

from backend.app.models.memory.document import Document, DocumentChunk, DocumentType


def test_document_creation(db_session: Session):
    doc = Document(
        path="/docs/README.md",
        filename="README.md",
        content_hash="abc123",
        doc_type=DocumentType.MARKDOWN,
        file_size=1024,
        language="markdown",
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    assert doc.id is not None
    assert doc.path == "/docs/README.md"
    assert doc.version == 1
    assert doc.doc_type == DocumentType.MARKDOWN
    assert doc.deleted_at is None


def test_document_chunk_creation(db_session: Session):
    doc = Document(
        path="/docs/guide.md",
        filename="guide.md",
        content_hash="def456",
        doc_type=DocumentType.MARKDOWN,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    chunk = DocumentChunk(
        document_id=doc.id,
        content="# Introduction\n\nThis is a guide.",
        chunk_index=0,
        start_offset=0,
        end_offset=35,
        token_count=9,
        chunk_type="heading",
        language="markdown",
        context_before=None,
        context_after="This is a guide.",
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)

    assert chunk.id is not None
    assert chunk.document_id == doc.id
    assert chunk.chunk_index == 0
    assert chunk.token_count == 9


def test_document_cascade_delete(db_session: Session):
    doc = Document(
        path="/docs/temp.md",
        filename="temp.md",
        content_hash="ghi789",
        doc_type=DocumentType.MARKDOWN,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    chunk1 = DocumentChunk(document_id=doc.id, content="chunk 1", chunk_index=0, token_count=2)
    chunk2 = DocumentChunk(document_id=doc.id, content="chunk 2", chunk_index=1, token_count=2)
    db_session.add_all([chunk1, chunk2])
    db_session.commit()

    db_session.delete(doc)
    db_session.commit()

    remaining = db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    assert len(remaining) == 0
