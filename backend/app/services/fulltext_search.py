"""PostgreSQL full-text search using tsvector/tsquery."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import Text, cast, func, text
from sqlalchemy.orm import Query, Session

logger = logging.getLogger(__name__)


@dataclass
class FullTextResult:
    content: str
    file_path: str
    rank: float
    source: str  # "code" or "document"
    chunk_id: int | None = None
    document_id: int | None = None
    language: str | None = None
    chunk_type: str | None = None


class FullTextSearch:
    """PostgreSQL full-text search using tsvector/tsquery with GIN indexes."""

    def __init__(self, db: Session):
        self._db = db

    def search_code(
        self,
        query: str,
        repo_id: int | None = None,
        language: str | None = None,
        limit: int = 20,
    ) -> list[FullTextResult]:
        try:
            tsquery = func.plainto_tsquery("english", query)
            tsvector = func.to_tsvector("english", cast("content", Text))

            rank = func.ts_rank(tsvector, tsquery)

            q: Query = (
                self._db.query(
                    text("content"),
                    text("file_path"),
                    rank.label("rank"),
                    text("id"),
                    text("language"),
                )
                .select_from(text("code_chunks"))
                .filter(text("to_tsvector('english', content) @@ plainto_tsquery('english', :query)"))
                .params(query=query)
                .order_by(text("rank DESC"))
                .limit(limit)
            )

            if repo_id is not None:
                q = q.filter(text("repo_id = :repo_id")).params(repo_id=repo_id)
            if language is not None:
                q = q.filter(text("language = :language")).params(language=language)

            rows = q.all()
            return [
                FullTextResult(
                    content=row[0][:500],
                    file_path=row[1],
                    rank=float(row[2]),
                    source="code",
                    chunk_id=row[3],
                    language=row[4],
                )
                for row in rows
            ]
        except Exception as e:
            logger.warning("Full-text search on code_chunks failed: %s", e)
            return []

    def search_documents(
        self,
        query: str,
        doc_type: str | None = None,
        limit: int = 20,
    ) -> list[FullTextResult]:
        try:
            q: Query = (
                self._db.query(
                    text("content"),
                    text("document_id"),
                    text("ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query))").label("rank"),
                )
                .select_from(text("document_chunks"))
                .filter(text("to_tsvector('english', content) @@ plainto_tsquery('english', :query)"))
                .params(query=query)
                .order_by(text("rank DESC"))
                .limit(limit)
            )

            if doc_type is not None:
                q = q.join(text("documents"), text("document_chunks.document_id = documents.id"))
                q = q.filter(text("documents.doc_type = :doc_type")).params(doc_type=doc_type)

            rows = q.all()
            return [
                FullTextResult(
                    content=row[0][:500],
                    file_path="",
                    rank=float(row[2]),
                    source="document",
                    document_id=row[1],
                )
                for row in rows
            ]
        except Exception as e:
            logger.warning("Full-text search on document_chunks failed: %s", e)
            return []


_fulltext_search: FullTextSearch | None = None


def get_fulltext_search(db: Session) -> FullTextSearch:
    global _fulltext_search
    if _fulltext_search is None:
        _fulltext_search = FullTextSearch(db)
    return _fulltext_search
