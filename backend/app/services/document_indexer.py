"""Document indexer — indexes non-code files into Document + DocumentChunk models."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.core.vector_db import VectorDB, get_vector_db
from backend.app.models.document import Document, DocumentChunk, DocumentType
from backend.app.services.embedding_cache import EmbeddingCacheService, get_embedding_cache
from backend.app.services.embedding_service import EmbeddingService, get_embedding_service
from backend.app.services.semantic_chunker import SemanticChunker

logger = logging.getLogger(__name__)

EMBED_BATCH_SIZE = 32

DOC_TYPE_MAP: dict[str, DocumentType] = {
    ".md": DocumentType.MARKDOWN,
    ".markdown": DocumentType.MARKDOWN,
    ".rst": DocumentType.MARKDOWN,
    ".txt": DocumentType.TEXT,
    ".log": DocumentType.TEXT,
    ".csv": DocumentType.TEXT,
    ".json": DocumentType.TEXT,
    ".yaml": DocumentType.TEXT,
    ".yml": DocumentType.TEXT,
    ".toml": DocumentType.TEXT,
    ".xml": DocumentType.TEXT,
    ".html": DocumentType.TEXT,
    ".css": DocumentType.TEXT,
    ".ipynb": DocumentType.NOTEBOOK,
    ".pdf": DocumentType.PDF,
}

SKIP_DIRS: set[str] = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".next", "target", ".cache",
}


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _detect_doc_type(path: str) -> DocumentType:
    ext = Path(path).suffix.lower()
    return DOC_TYPE_MAP.get(ext, DocumentType.OTHER)


class DocumentIndexer:
    """Indexes non-code files into Document + DocumentChunk models."""

    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService | None = None,
        embedding_cache: EmbeddingCacheService | None = None,
        vector_db: VectorDB | None = None,
    ):
        self._db = db
        self._embedder = embedding_service or get_embedding_service()
        self._cache = embedding_cache or get_embedding_cache(db)
        self._vector_db = vector_db or get_vector_db()
        self._chunker = SemanticChunker(max_tokens=800, overlap_tokens=150)

    def index_file(self, file_path: str, force: bool = False) -> bool:
        if not os.path.isfile(file_path):
            return False

        content_hash = _file_hash(file_path)
        existing = self._db.query(Document).filter(Document.path == file_path).first()

        if existing and existing.content_hash == content_hash and not force:
            return False

        try:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            logger.warning("Failed to read %s: %s", file_path, e)
            return False

        doc_type = _detect_doc_type(file_path)
        if doc_type == DocumentType.PDF:
            logger.info("PDF indexing not yet implemented: %s", file_path)
            return False

        if existing:
            doc = existing
            doc.content_hash = content_hash
            doc.version += 1
            doc.file_size = os.path.getsize(file_path)
            self._delete_old_chunks(doc.id)
        else:
            doc = Document(
                path=file_path,
                filename=Path(file_path).name,
                content_hash=content_hash,
                doc_type=doc_type,
                file_size=os.path.getsize(file_path),
            )
            self._db.add(doc)
            self._db.flush()

        chunks = self._chunker.chunk(content, doc_type, file_path)
        self._store_chunks(doc, chunks)
        self._embed_and_upsert(doc, chunks)

        doc.last_indexed_at = __import__("datetime").datetime.utcnow()
        self._db.commit()
        logger.info("Indexed %s (%d chunks, version=%d)", file_path, len(chunks), doc.version)
        return True

    def index_directory(self, dir_path: str, force: bool = False) -> dict:
        stats = {"files_scanned": 0, "files_indexed": 0, "files_skipped": 0, "errors": 0}

        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                fpath = os.path.join(root, fname)
                doc_type = _detect_doc_type(fpath)
                if doc_type == DocumentType.OTHER:
                    stats["files_skipped"] += 1
                    continue

                stats["files_scanned"] += 1
                try:
                    if self.index_file(fpath, force=force):
                        stats["files_indexed"] += 1
                    else:
                        stats["files_skipped"] += 1
                except Exception as e:
                    logger.warning("Error indexing %s: %s", fpath, e)
                    stats["errors"] += 1

        return stats

    def remove_file(self, file_path: str) -> bool:
        doc = self._db.query(Document).filter(Document.path == file_path).first()
        if not doc:
            return False

        self._delete_old_chunks(doc.id)
        self._db.delete(doc)
        self._db.commit()
        logger.info("Removed document: %s", file_path)
        return True

    def _delete_old_chunks(self, document_id: int) -> None:
        chunks = self._db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        embedding_ids = [c.embedding_id for c in chunks if c.embedding_id]
        if embedding_ids:
            try:
                self._vector_db.delete("cortex_memory", embedding_ids)
            except Exception as e:
                logger.warning("Failed to delete vectors: %s", e)
        for chunk in chunks:
            self._db.delete(chunk)
        self._db.flush()

    def _store_chunks(self, doc: Document, chunks: list) -> None:
        for i, sc in enumerate(chunks):
            db_chunk = DocumentChunk(
                document_id=doc.id,
                content=sc.content,
                chunk_index=i,
                start_offset=sc.start_offset,
                end_offset=sc.end_offset,
                token_count=sc.token_count,
                chunk_type=sc.chunk_type,
                language=sc.language,
                context_before=sc.context_before,
                context_after=sc.context_after,
            )
            self._db.add(db_chunk)
        self._db.flush()

    def _embed_and_upsert(self, doc: Document, chunks: list) -> None:
        db_chunks = (
            self._db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == doc.id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

        texts = [c.content for c in db_chunks]
        embeddings = self._embedder.embed_batch(texts)

        points = []
        for db_chunk, embedding in zip(db_chunks, embeddings, strict=False):
            embedding_id = self._embedder.compute_embedding_id(db_chunk.content)
            db_chunk.embedding_id = embedding_id
            points.append({
                "id": embedding_id,
                "vector": embedding,
                "payload": {
                    "document_id": doc.id,
                    "chunk_id": db_chunk.id,
                    "path": doc.path,
                    "doc_type": doc.doc_type.value,
                    "chunk_type": db_chunk.chunk_type,
                    "language": db_chunk.language,
                },
            })

        for i in range(0, len(points), EMBED_BATCH_SIZE):
            batch = points[i : i + EMBED_BATCH_SIZE]
            try:
                self._vector_db.upsert("cortex_memory", batch)
            except Exception as e:
                logger.warning("Failed to upsert vectors: %s", e)


_document_indexer: DocumentIndexer | None = None


def get_document_indexer(db: Session) -> DocumentIndexer:
    global _document_indexer
    if _document_indexer is None:
        _document_indexer = DocumentIndexer(db)
    return _document_indexer
