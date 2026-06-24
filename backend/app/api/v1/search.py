"""Unified search API with enhanced retrieval."""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.hybrid_retrieval import HybridRetrievalV2
from backend.app.services.retrieval_metrics import get_retrieval_metrics

logger = logging.getLogger(__name__)
router = APIRouter()


def encode_cursor(score: float, file_path: str, document_id: int | None = None) -> str:
    """Encode pagination cursor from last result."""
    data = {"score": score, "file_path": file_path, "document_id": document_id}
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    """Decode pagination cursor."""
    try:
        return json.loads(base64.urlsafe_b64decode(cursor.encode()))
    except Exception:
        return {}


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    repo_id: int | None = None
    max_results: int = Field(default=20, ge=1, le=50)
    sources: list[str] = Field(default=["vector", "fulltext"])
    diversity: float = Field(default=0.3, ge=0.0, le=1.0)
    cursor: str | None = None  # Base64-encoded cursor for pagination
    node_type: str | None = None  # Filter by node type (function, class, etc.)
    language: str | None = None  # Filter by programming language


class SearchResult(BaseModel):
    content: str
    source: str
    score: float
    file_path: str = ""
    document_id: int | None = None
    language: str | None = None
    chunk_type: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    query: str
    next_cursor: str | None = None
    has_more: bool = False


@router.post("/search", response_model=SearchResponse)
async def unified_search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    _user: Any = Depends(get_current_user),
):
    try:
        retrieval = HybridRetrievalV2(db)
        start_time = time.time()

        # Fetch extra results when using cursor to have room for filtering
        fetch_limit = request.max_results + 10 if request.cursor else request.max_results
        results = retrieval.retrieve(
            query=request.query,
            repo_id=request.repo_id,
            limit=fetch_limit,
            sources=request.sources,
            diversity_penalty=request.diversity,
            node_type=request.node_type,
            language=request.language,
        )
        latency_ms = (time.time() - start_time) * 1000

        # Apply cursor-based filtering (keyset pagination)
        if request.cursor:
            cursor_data = decode_cursor(request.cursor)
            if cursor_data:
                cursor_score = cursor_data.get("score", 0)
                cursor_file_path = cursor_data.get("file_path", "")
                cursor_doc_id = cursor_data.get("document_id")

                filtered = []
                for r in results:
                    # Skip results that are before or equal to the cursor position
                    if r.score > cursor_score or (
                        r.score == cursor_score
                        and (
                            r.file_path > cursor_file_path
                            or (
                                r.file_path == cursor_file_path
                                and r.document_id is not None
                                and cursor_doc_id is not None
                                and r.document_id > cursor_doc_id
                            )
                        )
                    ):
                        filtered.append(r)
                results = filtered

        sources_used = list(set(r.source for r in results)) if results else []
        top_score = results[0].score if results else 0.0
        get_retrieval_metrics().log_search(
            query=request.query,
            result_count=len(results),
            sources_used=sources_used,
            latency_ms=latency_ms,
            top_score=top_score,
        )

        # Determine if there are more results and generate next_cursor
        has_more = len(results) > request.max_results
        page_results = results[: request.max_results]

        next_cursor = None
        if has_more and page_results:
            last = page_results[-1]
            next_cursor = encode_cursor(last.score, last.file_path, last.document_id)

        return SearchResponse(
            results=[
                SearchResult(
                    content=r.content[:500],
                    source=r.source,
                    score=r.score,
                    file_path=r.file_path,
                    document_id=r.document_id,
                    language=r.language,
                    chunk_type=r.chunk_type,
                )
                for r in page_results
            ],
            total=len(page_results),
            query=request.query,
            next_cursor=next_cursor,
            has_more=has_more,
        )
    except Exception as e:
        logger.error("Search failed: %s", e)
        raise HTTPException(status_code=500, detail="Search failed. Please try again.")


@router.get("/search", response_model=SearchResponse)
async def unified_search_get(
    query: str,
    repo_id: int | None = None,
    max_results: int = 20,
    cursor: str | None = None,
    db: Session = Depends(get_db),
    _user: Any = Depends(get_current_user),
):
    request = SearchRequest(query=query, repo_id=repo_id, max_results=max_results, cursor=cursor)
    return await unified_search(request, db, _user)


class SearchAnswerRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    repo_id: int | None = None
    max_results: int = Field(default=10, ge=1, le=50)


class SearchAnswerResponse(BaseModel):
    query: str
    answer: str
    results: list[SearchResult]


@router.post("/search/answer", response_model=SearchAnswerResponse)
async def search_with_answer(
    payload: SearchAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search and synthesize an AI answer from results."""
    from backend.app.services.llm.manager import llm_manager
    from backend.app.services.llm.provider import LLMMessage

    retrieval = HybridRetrievalV2(db)
    results = retrieval.retrieve(
        query=payload.query,
        repo_id=payload.repo_id,
        limit=payload.max_results or 10,
    )

    context_parts: list[str] = []
    for r in results:
        context_parts.append(f"[{r.source}: {r.file_path or 'unknown'}]\n{r.content[:500]}")

    context = "\n\n".join(context_parts[:10])

    try:
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are Cortex, a helpful AI assistant. Answer the user's question using the provided context. "
                    "Be concise and cite sources. If the context doesn't contain enough info, say so."
                ),
            ),
            LLMMessage(role="user", content=f"Context:\n{context}\n\nQuestion: {payload.query}"),
        ]
        response = await llm_manager.chat(messages, max_tokens=1024, temperature=0.3)
        answer = response.content
    except RuntimeError:
        answer = "LLM not configured. Enable a local model in Settings > Models to get AI-powered answers."

    return {
        "query": payload.query,
        "answer": answer,
        "results": [
            {
                "content": r.content[:500],
                "source": r.source,
                "score": r.score,
                "file_path": r.file_path,
                "document_id": r.document_id,
            }
            for r in results[:5]
        ],
    }
