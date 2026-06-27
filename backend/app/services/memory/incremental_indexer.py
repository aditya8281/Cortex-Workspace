"""Incremental indexer — only re-indexes files that changed since last scan."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.core.vector_db import get_vector_db
from backend.app.models.file_index import IndexedFile
from backend.app.models.repo_index import CodeChunk, RepoIndex
from backend.app.services.chunker import SKIP_DIRS, Chunk, chunk_code, chunk_text, detect_language
from backend.app.services.embedding_service import get_embedding_service
from backend.app.services.indexing_rules import IndexingRules

logger = logging.getLogger(__name__)

CODE_COLLECTION = "cortex_code"
EMBED_BATCH_SIZE = 32
TRACKED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".rs",
    ".go",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".sql",
    ".sh",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
}


@dataclass
class IndexResult:
    repo_id: int
    files_scanned: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    files_deleted: int = 0
    files_errors: int = 0
    chunks_created: int = 0
    languages: dict[str, int] = field(default_factory=dict)
    status: str = "completed"


class IncrementalIndexer:
    """Index repositories with hash-based change detection."""

    def __init__(self, db: Session):
        self.db = db

    def index_repo(self, repo_id: int, force: bool = False, rules: IndexingRules | None = None) -> IndexResult:
        """Index only changed files in a repository.

        Args:
            repo_id: ID of the RepoIndex record.
            force: If True, re-index all files regardless of hash.
        """
        repo = self.db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
        if not repo:
            raise ValueError(f"Repo {repo_id} not found")

        path = Path(repo.repo_path)
        if not path.is_dir():
            raise ValueError(f"Repository path does not exist: {repo.repo_path}")

        existing_files = {
            f.file_path: f for f in self.db.query(IndexedFile).filter(IndexedFile.repo_id == repo_id).all()
        }

        all_files = self._walk_repository(path, rules=rules)
        current_files: dict[str, Path] = {}
        for file_path in all_files:
            rel = str(file_path.relative_to(path))
            current_files[rel] = file_path

        languages: dict[str, int] = {}
        result = IndexResult(repo_id=repo_id)

        for rel_path, file_path in current_files.items():
            result.files_scanned += 1
            lang = detect_language(str(file_path))
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

            existing = existing_files.get(rel_path)

            # --- Mtime/size pre-filter ---
            try:
                stat = file_path.stat()
            except OSError:
                result.files_errors += 1
                if existing:
                    existing.status = "error"
                continue

            if not force and existing and existing.mtime == stat.st_mtime and existing.file_size == stat.st_size:
                result.files_skipped += 1
                continue

            # --- Hash check (only if mtime/size changed) ---
            current_hash = self._file_hash(file_path)

            if not force and existing and existing.file_hash == current_hash:
                # File content unchanged — just update stat metadata
                existing.mtime = stat.st_mtime
                existing.file_size = stat.st_size
                result.files_skipped += 1
                continue

            try:
                chunks = self._index_file(file_path, rel_path, lang)
                chunk_count = len(chunks)

                if existing:
                    existing.file_hash = current_hash
                    existing.file_size = stat.st_size
                    existing.mtime = stat.st_mtime
                    existing.last_indexed_at = datetime.now(timezone.utc)
                    existing.chunk_count = chunk_count
                    existing.status = "indexed"
                else:
                    self.db.add(
                        IndexedFile(
                            repo_id=repo_id,
                            file_path=rel_path,
                            file_hash=current_hash,
                            file_size=stat.st_size,
                            mtime=stat.st_mtime,
                            last_indexed_at=datetime.now(timezone.utc),
                            chunk_count=chunk_count,
                            status="indexed",
                        )
                    )

                result.files_indexed += 1
                result.chunks_created += chunk_count
            except Exception as exc:
                logger.warning("Error indexing %s: %s", rel_path, exc)
                result.files_errors += 1
                if existing:
                    existing.status = "error"

        # --- Deleted file cleanup ---
        stale_files = set(existing_files.keys()) - set(current_files.keys())
        for stale_path in stale_files:
            existing = existing_files[stale_path]
            self._remove_file(existing)
            result.files_deleted += 1

        result.languages = languages

        repo.total_files = result.files_scanned
        repo.total_chunks = result.chunks_created
        repo.last_indexed_at = datetime.now(timezone.utc)
        repo.status = "completed"
        self.db.commit()

        logger.info(
            "Indexed repo %d: %d indexed, %d skipped, %d deleted, %d errors, %d chunks",
            repo_id,
            result.files_indexed,
            result.files_skipped,
            result.files_deleted,
            result.files_errors,
            result.chunks_created,
        )
        return result

    def _remove_file(self, indexed_file: IndexedFile) -> None:
        """Remove a stale IndexedFile and all its associated data."""
        rel_path = indexed_file.file_path

        # Collect embedding IDs from old chunks (batch query)
        old_chunks = (
            self.db.query(CodeChunk)
            .filter(
                CodeChunk.repo_id == indexed_file.repo_id,
                CodeChunk.file_path == rel_path,
            )
            .all()
        )
        embedding_ids: list[str] = [c.embedding_id for c in old_chunks if c.embedding_id]

        # Batch delete vector DB entries
        if embedding_ids:
            try:
                vdb = get_vector_db()
                vdb.delete(CODE_COLLECTION, embedding_ids)
            except Exception as exc:
                logger.warning("Failed to delete vectors for %s: %s", rel_path, exc)

        # Batch delete CodeChunk records
        for chunk in old_chunks:
            self.db.delete(chunk)

        # Delete the IndexedFile record
        self.db.delete(indexed_file)
        self.db.flush()
        logger.info("Removed stale file: %s (%d chunks, %d vectors)", rel_path, len(old_chunks), len(embedding_ids))

    def _walk_repository(self, path: Path, rules: IndexingRules | None = None) -> list[Path]:
        """Walk repository files, skipping ignored directories.

        If rules is provided, applies additional IndexingRules filtering.
        """
        follow_symlinks = bool(rules and rules._config and rules._config.follow_symlinks)
        files: list[Path] = []
        for root, dirs, filenames in path.walk(follow_symlinks=follow_symlinks):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.is_file() and file_path.suffix in TRACKED_EXTENSIONS:
                    if rules and not rules.should_index(str(file_path), str(path)):
                        continue
                    files.append(file_path)
        return sorted(files)

    def _file_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of file contents."""
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _index_file(self, file_path: Path, rel_path: str, lang: str | None) -> list[Chunk]:
        """Index a single file: chunk, embed, store in vector DB."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise ValueError(f"Cannot read {file_path}: {exc}") from exc

        chunks = chunk_text(content, rel_path) if lang in {"markdown", "text"} else chunk_code(content, rel_path)

        if not chunks:
            return []

        # Remove old chunks for this file
        old_chunks = self.db.query(CodeChunk).filter(CodeChunk.file_path == rel_path).all()
        if old_chunks:
            embedding_ids = [c.embedding_id for c in old_chunks if c.embedding_id]
            if embedding_ids:
                vdb = get_vector_db()
                vdb.delete(CODE_COLLECTION, embedding_ids)
            for c in old_chunks:
                self.db.delete(c)
            self.db.flush()

        # Create new chunk records
        repo_id = self._get_repo_id_for_file(rel_path)

        db_chunks: list[CodeChunk] = []
        for ch in chunks:
            chunk = CodeChunk(
                repo_id=repo_id,
                file_path=ch.file_path,
                chunk_index=ch.chunk_index,
                content=ch.content,
                language=ch.language,
                symbol_type=ch.symbol_type,
                symbol_name=ch.symbol_name,
                start_line=ch.start_line,
                end_line=ch.end_line,
            )
            self.db.add(chunk)
            db_chunks.append(chunk)
        self.db.flush()

        # Embed and store in vector DB
        self._embed_chunks(db_chunks)

        return chunks

    def _get_repo_id_for_file(self, rel_path: str) -> int:
        """Find the repo_id that owns this file path."""
        result = (
            self.db.query(IndexedFile.repo_id)
            .filter(IndexedFile.file_path == rel_path)
            .order_by(IndexedFile.id.desc())
            .first()
        )
        if result:
            return result[0]
        repo = self.db.query(RepoIndex).order_by(RepoIndex.id.desc()).first()
        return repo.id if repo else 0

    def _embed_chunks(self, chunks: list[CodeChunk]) -> None:
        """Embed a batch of code chunks and store in vector DB."""
        embedding_svc = get_embedding_service()
        vdb = get_vector_db()

        batch: list[CodeChunk] = []
        for chunk in chunks:
            batch.append(chunk)
            if len(batch) >= EMBED_BATCH_SIZE:
                self._embed_batch(batch, embedding_svc, vdb)
                batch.clear()

        if batch:
            self._embed_batch(batch, embedding_svc, vdb)

    def _embed_batch(self, chunks: list[CodeChunk], embedding_svc, vdb) -> None:
        """Embed a batch of code chunks."""
        texts = [c.content for c in chunks]
        vectors = embedding_svc.embed_batch(texts)

        points = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            embedding_id = embedding_svc.compute_embedding_id(chunk.content)
            chunk.embedding_id = embedding_id
            points.append(
                {
                    "id": embedding_id,
                    "vector": vector,
                    "payload": {
                        "repo_id": chunk.repo_id,
                        "chunk_id": chunk.id,
                        "file_path": chunk.file_path,
                        "content": chunk.content,
                        "language": chunk.language,
                        "symbol_type": chunk.symbol_type,
                        "symbol_name": chunk.symbol_name,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                    },
                }
            )

        if points:
            vdb.upsert(CODE_COLLECTION, points)
        self.db.flush()
