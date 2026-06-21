"""Document indexer — indexes non-code files into Document + DocumentChunk models.

Enhanced with proper MIME type detection via Python's mimetypes module, encoding
detection using chardet (when available), and MIME-to-DocumentType mapping.
Inspired by sist2's file handling approach.
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.core.vector_db import VectorDB, get_vector_db
from backend.app.models.document import Document, DocumentChunk, DocumentType
from backend.app.services.embedding_cache import EmbeddingCacheService, get_embedding_cache
from backend.app.services.embedding_service import EmbeddingService, get_embedding_service
from backend.app.services.parsers import (
    ArchiveParser,
    DocxParser,
    EPUBParser,
    FontParser,
    GISParser,
    HTMLParser,
    ICalParser,
    MarkdownParser,
    MediaParser,
    NotebookParser,
    OpenDocumentParser,
    PDFParser,
    PptxParser,
    VCardParser,
    XlsxParser,
)
from backend.app.services.semantic_chunker import SemanticChunker

logger = logging.getLogger(__name__)

EMBED_BATCH_SIZE = 32

_PARSERS: dict[DocumentType, object] = {
    DocumentType.PDF: PDFParser(),
    DocumentType.MARKDOWN: MarkdownParser(),
    DocumentType.NOTEBOOK: NotebookParser(),
    DocumentType.DOCX: DocxParser(),
    DocumentType.EPUB: EPUBParser(),
    DocumentType.HTML: HTMLParser(),
    DocumentType.PPTX: PptxParser(),
    DocumentType.XLSX: XlsxParser(),
    DocumentType.OPENDOCUMENT: OpenDocumentParser(),
    DocumentType.VCARD: VCardParser(),
    DocumentType.ICAL: ICalParser(),
    DocumentType.ARCHIVE: ArchiveParser(),
    DocumentType.IMAGE: MediaParser(),
    DocumentType.AUDIO: MediaParser(),
    DocumentType.VIDEO: MediaParser(),
    DocumentType.FONT: FontParser(),
    DocumentType.GIS: GISParser(),
}

# Extension-based fallback map (used when mimetypes module can't resolve).
DOC_TYPE_MAP: dict[str, DocumentType] = {
    ".md": DocumentType.MARKDOWN,
    ".markdown": DocumentType.MARKDOWN,
    ".rst": DocumentType.MARKDOWN,
    ".txt": DocumentType.TEXT,
    ".log": DocumentType.TEXT,
    ".csv": DocumentType.TEXT,
    ".json": DocumentType.TEXT,
    ".jsonl": DocumentType.TEXT,
    ".ndjson": DocumentType.TEXT,
    ".yaml": DocumentType.TEXT,
    ".yml": DocumentType.TEXT,
    ".toml": DocumentType.TEXT,
    ".xml": DocumentType.TEXT,
    ".css": DocumentType.TEXT,
    ".ipynb": DocumentType.NOTEBOOK,
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
    ".epub": DocumentType.EPUB,
    ".html": DocumentType.HTML,
    ".htm": DocumentType.HTML,
    ".pptx": DocumentType.PPTX,
    ".xlsx": DocumentType.XLSX,
    ".odt": DocumentType.OPENDOCUMENT,
    ".ods": DocumentType.OPENDOCUMENT,
    ".odp": DocumentType.OPENDOCUMENT,
    ".vcf": DocumentType.VCARD,
    ".ics": DocumentType.ICAL,
    ".zip": DocumentType.ARCHIVE,
    ".tar": DocumentType.ARCHIVE,
    ".gz": DocumentType.ARCHIVE,
    ".bz2": DocumentType.ARCHIVE,
    ".7z": DocumentType.ARCHIVE,
    ".rar": DocumentType.ARCHIVE,
    ".jpg": DocumentType.IMAGE,
    ".jpeg": DocumentType.IMAGE,
    ".png": DocumentType.IMAGE,
    ".gif": DocumentType.IMAGE,
    ".bmp": DocumentType.IMAGE,
    ".tiff": DocumentType.IMAGE,
    ".webp": DocumentType.IMAGE,
    ".svg": DocumentType.IMAGE,
    ".mp3": DocumentType.AUDIO,
    ".wav": DocumentType.AUDIO,
    ".flac": DocumentType.AUDIO,
    ".ogg": DocumentType.AUDIO,
    ".m4a": DocumentType.AUDIO,
    ".wma": DocumentType.AUDIO,
    ".mp4": DocumentType.VIDEO,
    ".mkv": DocumentType.VIDEO,
    ".avi": DocumentType.VIDEO,
    ".mov": DocumentType.VIDEO,
    ".wmv": DocumentType.VIDEO,
    ".webm": DocumentType.VIDEO,
    ".ttf": DocumentType.FONT,
    ".otf": DocumentType.FONT,
    ".woff": DocumentType.FONT,
    ".woff2": DocumentType.FONT,
    ".sh": DocumentType.CODE,
    ".py": DocumentType.CODE,
    ".js": DocumentType.CODE,
    ".ts": DocumentType.CODE,
    ".go": DocumentType.CODE,
    ".rs": DocumentType.CODE,
    ".java": DocumentType.CODE,
    ".c": DocumentType.CODE,
    ".cpp": DocumentType.CODE,
    ".h": DocumentType.CODE,
    ".geojson": DocumentType.GIS,
    ".kml": DocumentType.GIS,
    ".gpx": DocumentType.GIS,
}

# MIME type -> DocumentType mapping for when mimetypes detects a MIME type
# that doesn't directly correspond to an extension in DOC_TYPE_MAP.
MIME_TYPE_MAP: dict[str, DocumentType] = {
    "text/markdown": DocumentType.MARKDOWN,
    "text/x-markdown": DocumentType.MARKDOWN,
    "text/x-rst": DocumentType.MARKDOWN,
    "text/plain": DocumentType.TEXT,
    "text/csv": DocumentType.TEXT,
    "text/json": DocumentType.TEXT,
    "application/json": DocumentType.TEXT,
    "application/x-yaml": DocumentType.TEXT,
    "text/yaml": DocumentType.TEXT,
    "text/toml": DocumentType.TEXT,
    "application/xml": DocumentType.TEXT,
    "text/xml": DocumentType.TEXT,
    "text/html": DocumentType.HTML,
    "text/css": DocumentType.TEXT,
    "application/x-ipynb+json": DocumentType.NOTEBOOK,
    "application/pdf": DocumentType.PDF,
    # Code-like text files that may end up in document indexing
    "text/x-python": DocumentType.CODE,
    "text/x-javascript": DocumentType.CODE,
    "text/x-typescript": DocumentType.CODE,
    "text/x-c": DocumentType.CODE,
    "text/x-c++": DocumentType.CODE,
    "text/x-java": DocumentType.CODE,
    "text/x-go": DocumentType.CODE,
    "text/x-rust": DocumentType.CODE,
    "text/x-shellscript": DocumentType.CODE,
}

SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    "dist",
    "build",
    ".next",
    "target",
    ".cache",
}

# chardet availability
try:
    import chardet  # type: ignore[import-untyped]

    _CHARDET_AVAILABLE = True
except ImportError:
    _CHARDET_AVAILABLE = False


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _detect_encoding(file_path: str) -> str:
    """Detect file encoding using chardet if available, else default to utf-8."""
    if not _CHARDET_AVAILABLE:
        return "utf-8"

    try:
        with open(file_path, "rb") as f:
            raw = f.read(min(os.path.getsize(file_path), 1024 * 1024))
        result = chardet.detect(raw)
        encoding = result.get("encoding") or "utf-8"
        confidence = result.get("confidence", 0)

        # Low-confidence detections are unreliable; fall back to utf-8.
        if confidence < 0.6:
            logger.debug(
                "Low-confidence encoding detection (%s, %.0f%%) for %s, using utf-8",
                encoding,
                confidence * 100,
                file_path,
            )
            return "utf-8"

        return encoding
    except Exception as e:
        logger.debug("Encoding detection failed for %s: %s", file_path, e)
        return "utf-8"


def detect_mime_type(file_path: str) -> str | None:
    """Detect MIME type using Python's mimetypes module.

    Returns the MIME type string or None if undetectable.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type


def _detect_doc_type(path: str) -> DocumentType:
    """Detect document type using mimetypes with extension fallback."""
    # 1. Try mimetypes module first
    mime_type = detect_mime_type(path)
    if mime_type and mime_type in MIME_TYPE_MAP:
        return MIME_TYPE_MAP[mime_type]

    # 2. Fall back to extension map
    ext = Path(path).suffix.lower()
    if ext in DOC_TYPE_MAP:
        return DOC_TYPE_MAP[ext]

    # 3. Check if it's a generic text/* MIME type
    if mime_type and mime_type.startswith("text/"):
        return DocumentType.TEXT

    return DocumentType.OTHER


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

    def _extract_content(self, file_path: str, doc_type: DocumentType) -> str | None:
        parser = _PARSERS.get(doc_type)
        if parser is None:
            return self._read_text_file(file_path)
        try:
            parsed = parser.parse(file_path)
            return parsed.full_text
        except Exception as e:
            logger.warning(
                "Failed to parse %s with %s: %s, falling back to raw read",
                file_path,
                type(parser).__name__,
                e,
            )
            return self._read_text_file(file_path)

    def _read_text_file(self, file_path: str) -> str | None:
        """Read a text file with automatic encoding detection."""
        encoding = _detect_encoding(file_path)
        try:
            with open(file_path, encoding=encoding, errors="replace") as f:
                return f.read()
        except Exception as e:
            logger.warning("Failed to read %s with encoding %s: %s", file_path, encoding, e)
            return None

    def index_file(self, file_path: str, force: bool = False) -> bool:
        if not os.path.isfile(file_path):
            return False

        content_hash = _file_hash(file_path)
        existing = self._db.query(Document).filter(Document.path == file_path).first()

        if existing and existing.content_hash == content_hash and not force:
            return False

        doc_type = _detect_doc_type(file_path)
        content = self._extract_content(file_path, doc_type)
        if content is None:
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
            points.append(
                {
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
                }
            )

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
