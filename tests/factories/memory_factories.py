"""Factory functions for memory domain models."""

from backend.app.models.memory.document import Document, DocumentChunk
from backend.app.models.memory.storage_registry import StorageRegistry


def create_document(
    path: str | None = None,
    **kwargs,
) -> Document:
    """Create a Document model instance for testing."""
    from faker import Faker
    fake = Faker()
    return Document(
        id=kwargs.get("id", fake.uuid4()),
        path=path or f"/test/docs/{fake.file_name()}",
        filename=kwargs.get("filename", fake.file_name()),
        content_hash=kwargs.get("content_hash", fake.sha256()),
        doc_type=kwargs.get("doc_type", "text"),
        file_size=kwargs.get("file_size", fake.random_int(min=100, max=100000)),
        language=kwargs.get("language", "en"),
        version=kwargs.get("version", 1),
    )


def create_document_batch(count: int) -> list[Document]:
    """Create a batch of documents for testing."""
    return [create_document() for _ in range(count)]
