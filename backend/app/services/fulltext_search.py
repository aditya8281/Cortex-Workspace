"""PostgreSQL full-text search using tsvector/tsquery.

Enhanced with snippet highlighting (ts_headline), configurable BM25 field
weights, and query expansion via stemming.  Inspired by sist2's search
capabilities.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Simple English suffix-stemmer for query expansion.  Not a full Porter stemmer
# but covers the most common suffixes and keeps the dependency footprint zero.
_SUFFIX_RULES: list[tuple[str, str]] = [
    ("ies", "y"),
    ("ness", ""),
    ("ment", ""),
    ("tion", "te"),
    ("sion", "de"),
    ("able", ""),
    ("ible", ""),
    ("ful", ""),
    ("less", ""),
    ("ous", ""),
    ("ive", ""),
    ("ing", ""),
    ("edly", ""),
    ("ily", "y"),
    ("ly", ""),
    ("er", ""),
    ("ed", ""),
    ("es", "e"),
    ("s", ""),
]

# Default BM25 field weights for code search (column -> weight).
DEFAULT_CODE_WEIGHTS: dict[str, float] = {
    "content": 1.0,
    "symbol_name": 0.8,
    "file_path": 0.3,
    "language": 0.2,
}

# Default BM25 field weights for document search.
DEFAULT_DOC_WEIGHTS: dict[str, float] = {
    "content": 1.0,
    "filename": 0.5,
}


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
    snippet: str | None = None


def _stem_word(word: str) -> str:
    """Apply lightweight suffix-stripping to a single word."""
    lower = word.lower()
    for suffix, replacement in _SUFFIX_RULES:
        if len(lower) - len(suffix) >= 3 and lower.endswith(suffix):
            return lower[: -len(suffix)] + replacement
    return lower


def _expand_query(query: str) -> str:
    """Expand a query by adding stemmed variants of each term."""
    tokens = re.findall(r"\w+", query)
    if not tokens:
        return query

    expanded: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        stemmed = _stem_word(token)
        for variant in (token, stemmed):
            low = variant.lower()
            if low not in seen and len(low) >= 2:
                seen.add(low)
                expanded.append(low)

    return " ".join(expanded)


def _build_weighted_tsquery(
    query: str,
    config: dict[str, float],
) -> str:
    """Build a ts_rank_cd expression with field-specific weights.

    Returns the SQL fragment for ranking, using plainto_tsquery for each
    weighted field and summing the weighted ranks.
    """
    parts: list[str] = []
    for col, weight in config.items():
        parts.append(
            f"ts_rank_cd(to_tsvector('english', COALESCE({col}, '')), "
            f"plainto_tsquery('english', :query), 32) * {weight}"
        )
    return " + ".join(parts)


def _safe_snippet_length(length: int) -> int:
    """Clamp snippet_length to a safe range to prevent SQL injection."""
    return max(60, min(length, 1000))


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
        snippet_length: int = 300,
    ) -> list[FullTextResult]:
        try:
            safe_snippet = _safe_snippet_length(snippet_length)
            expanded = _expand_query(query)
            rank_expr = _build_weighted_tsquery(expanded, DEFAULT_CODE_WEIGHTS)

            snippet_expr = (
                f"ts_headline('english', COALESCE(content, ''), "
                f"plainto_tsquery('english', :query), "
                f"'StartSel=<<, StopSel=>>, MaxWords={safe_snippet}, "
                f"MinWords=60, MaxFragments=3')"
            )

            sql = text(f"""
                SELECT
                    content,
                    file_path,
                    ({rank_expr}) AS rank,
                    id,
                    language,
                    {snippet_expr} AS snippet
                FROM code_chunks
                WHERE to_tsvector('english', COALESCE(content, ''))
                      @@ plainto_tsquery('english', :query)
                ORDER BY rank DESC
                LIMIT :limit
            """)

            params: dict = {"query": expanded, "limit": limit}
            if repo_id is not None:
                sql = text(f"""
                    SELECT content, file_path, (rank), id, language, snippet
                    FROM (
                        SELECT
                            content,
                            file_path,
                            ({rank_expr}) AS rank,
                            id,
                            language,
                            {snippet_expr} AS snippet
                        FROM code_chunks
                        WHERE to_tsvector('english', COALESCE(content, ''))
                              @@ plainto_tsquery('english', :query)
                          AND repo_id = :repo_id
                    ) sub
                    ORDER BY rank DESC
                    LIMIT :limit
                """)
                params["repo_id"] = repo_id

            if language is not None:
                sql = text(f"""
                    SELECT content, file_path, (rank), id, language, snippet
                    FROM (
                        SELECT
                            content,
                            file_path,
                            ({rank_expr}) AS rank,
                            id,
                            language,
                            {snippet_expr} AS snippet
                        FROM code_chunks
                        WHERE to_tsvector('english', COALESCE(content, ''))
                              @@ plainto_tsquery('english', :query)
                          AND (:lang_filter IS NULL OR language = :lang_filter)
                          {"AND repo_id = :repo_id" if repo_id is not None else ""}
                    ) sub
                    ORDER BY rank DESC
                    LIMIT :limit
                """)
                params["lang_filter"] = language

            rows = self._db.execute(sql, params).fetchall()
            return [
                FullTextResult(
                    content=row[0][:500] if row[0] else "",
                    file_path=row[1] or "",
                    rank=float(row[2]) if row[2] else 0.0,
                    source="code",
                    chunk_id=row[3],
                    language=row[4],
                    snippet=row[5],
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("Full-text search on code_chunks failed: %s", e, exc_info=True)
            return []

    def search_documents(
        self,
        query: str,
        doc_type: str | None = None,
        limit: int = 20,
        snippet_length: int = 300,
    ) -> list[FullTextResult]:
        try:
            safe_snippet = _safe_snippet_length(snippet_length)
            expanded = _expand_query(query)
            rank_expr = _build_weighted_tsquery(expanded, DEFAULT_DOC_WEIGHTS)

            snippet_expr = (
                f"ts_headline('english', COALESCE(dc.content, ''), "
                f"plainto_tsquery('english', :query), "
                f"'StartSel=<<, StopSel=>>, MaxWords={safe_snippet}, "
                f"MinWords=60, MaxFragments=3')"
            )

            join_clause = ""
            filter_clause = ""
            params: dict = {"query": expanded, "limit": limit}

            if doc_type is not None:
                join_clause = "JOIN documents d ON dc.document_id = d.id"
                filter_clause = "AND d.doc_type = :doc_type"
                params["doc_type"] = doc_type

            sql = text(f"""
                SELECT
                    dc.content,
                    dc.document_id,
                    ({rank_expr}) AS rank,
                    {snippet_expr} AS snippet
                FROM document_chunks dc
                {join_clause}
                WHERE to_tsvector('english', COALESCE(dc.content, ''))
                      @@ plainto_tsquery('english', :query)
                {filter_clause}
                ORDER BY rank DESC
                LIMIT :limit
            """)

            rows = self._db.execute(sql, params).fetchall()
            return [
                FullTextResult(
                    content=row[0][:500] if row[0] else "",
                    file_path="",
                    rank=float(row[2]) if row[2] else 0.0,
                    source="document",
                    document_id=row[1],
                    snippet=row[3],
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("Full-text search on document_chunks failed: %s", e, exc_info=True)
            return []


def get_fulltext_search(db: Session) -> FullTextSearch:
    """Create a FullTextSearch instance for the given session."""
    return FullTextSearch(db)
