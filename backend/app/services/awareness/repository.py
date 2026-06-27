"""Repository scanner for code indexing."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.vector_db import get_vector_db
from backend.app.models.awareness.repo_index import CodeChunk, RepoIndex
from backend.app.services.intelligence.chunker import SKIP_DIRS, Chunk, chunk_code, chunk_text, detect_language
from backend.app.services.intelligence.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

CODE_COLLECTION = "cortex_code"
EMBED_BATCH_SIZE = 32


@dataclass
class ScanResult:
    repo_id: int
    repo_path: str
    repo_name: str
    files_scanned: int
    chunks_created: int
    languages: dict[str, int] = field(default_factory=dict)
    status: str = "completed"


@dataclass
class RepoStatus:
    repo_id: int
    repo_name: str
    status: str
    total_files: int
    total_chunks: int
    languages: dict[str, int] = field(default_factory=dict)


class RepoScanner:
    """Scan and index repositories for code understanding."""

    def __init__(self, db: Session):
        self.db = db

    def scan_repo(self, repo_path: str, user_id: int | None = None) -> ScanResult:
        """Scan a repository and index all code files."""
        path = Path(repo_path).expanduser().resolve()
        if not path.is_dir():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        repo_name = path.name
        files = self._walk_repository(path)
        languages: dict[str, int] = {}
        all_chunks: list[Chunk] = []

        for file_path in files:
            lang = detect_language(str(file_path))
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                logger.warning("Skipping unreadable file %s: %s", file_path, exc)
                continue

            if lang in {"markdown", "text"}:
                file_chunks = chunk_text(content, str(file_path))
            else:
                file_chunks = chunk_code(content, str(file_path))

            all_chunks.extend(file_chunks)

        # Create repo index record
        repo = RepoIndex(
            user_id=user_id,
            repo_path=str(path),
            repo_name=repo_name,
            primary_language=max(languages, key=lambda k: languages[k]) if languages else None,
            total_files=len(files),
            total_chunks=len(all_chunks),
            status="indexing",
        )
        self.db.add(repo)
        self.db.flush()

        # Create code chunk records
        for c in all_chunks:
            self.db.add(
                CodeChunk(
                    repo_id=repo.id,
                    file_path=c.file_path,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    language=c.language,
                    symbol_type=c.symbol_type,
                    symbol_name=c.symbol_name,
                    start_line=c.start_line,
                    end_line=c.end_line,
                )
            )
        self.db.flush()

        # Embed all chunks
        self._embed_chunks(repo.id)

        # Update repo status
        repo.status = "completed"
        repo.last_indexed_at = datetime.now(timezone.utc)
        self.db.commit()

        return ScanResult(
            repo_id=repo.id,
            repo_path=str(path),
            repo_name=repo_name,
            files_scanned=len(files),
            chunks_created=len(all_chunks),
            languages=languages,
            status="completed",
        )

    def _walk_repository(self, path: Path) -> list[Path]:
        """Walk repository files, skipping ignored directories."""
        files: list[Path] = []
        for root, dirs, filenames in os.walk(path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.is_file():
                    files.append(file_path)
        return sorted(files)

    def _embed_chunks(self, repo_id: int) -> None:
        """Embed all chunks for a repository and store in vector DB."""
        embedding_svc = get_embedding_service()
        vdb = get_vector_db()

        chunks = self.db.query(CodeChunk).filter(CodeChunk.repo_id == repo_id, CodeChunk.embedding_id.is_(None)).all()

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

    def get_repo_status(self, repo_id: int) -> RepoStatus | None:
        """Get status of an indexed repository."""
        repo = self.db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
        if not repo:
            return None

        language_rows = (
            self.db.query(CodeChunk.language, func.count(CodeChunk.id))
            .filter(CodeChunk.repo_id == repo_id)
            .group_by(CodeChunk.language)
            .all()
        )
        languages = {lang or "unknown": count for lang, count in language_rows}

        return RepoStatus(
            repo_id=repo.id,
            repo_name=repo.repo_name,
            status=repo.status,
            total_files=repo.total_files,
            total_chunks=repo.total_chunks,
            languages=languages,
        )

    def search_code(
        self,
        query: str,
        repo_id: int | None = None,
        language: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search code chunks using semantic similarity."""
        embedding_svc = get_embedding_service()
        vdb = get_vector_db()

        query_vector = embedding_svc.embed_single(query)

        filter_payload: dict[str, str | int] = {}
        if repo_id is not None:
            filter_payload["repo_id"] = repo_id
        if language is not None:
            filter_payload["language"] = language

        results = vdb.search(
            CODE_COLLECTION,
            query_vector,
            limit=limit * 2,
            filter_payload=filter_payload if filter_payload else None,
        )

        return results[:limit]
