"""Knowledge system health and stats API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.document import Document, DocumentChunk
from backend.app.models.graph import GraphEdge, GraphNode
from backend.app.models.repo_index import CodeChunk, RepoIndex
from backend.app.services.retrieval_metrics import get_retrieval_metrics

router = APIRouter()


class KnowledgeHealth(BaseModel):
    status: str
    documents_indexed: int
    total_chunks: int
    graph_nodes: int
    graph_edges: int
    repos_indexed: int
    code_chunks: int


class KnowledgeStats(BaseModel):
    documents_by_type: dict[str, int]
    chunks_by_language: dict[str, int]
    avg_chunks_per_document: float
    graph_edge_types: dict[str, int]


@router.get("/knowledge/health", response_model=KnowledgeHealth)
async def knowledge_health(
    db: Session = Depends(get_db),
    _user: Any = Depends(get_current_user),
):
    doc_count = db.query(Document).filter(Document.deleted_at.is_(None)).count()
    chunk_count = db.query(DocumentChunk).count()
    node_count = db.query(GraphNode).count()
    edge_count = db.query(GraphEdge).count()
    repo_count = db.query(RepoIndex).count()
    code_chunk_count = db.query(CodeChunk).count()

    return KnowledgeHealth(
        status="healthy",
        documents_indexed=doc_count,
        total_chunks=chunk_count,
        graph_nodes=node_count,
        graph_edges=edge_count,
        repos_indexed=repo_count,
        code_chunks=code_chunk_count,
    )


@router.get("/knowledge/stats", response_model=KnowledgeStats)
async def knowledge_stats(
    db: Session = Depends(get_db),
    _user: Any = Depends(get_current_user),
):
    type_rows = (
        db.query(Document.doc_type, func.count(Document.id))
        .filter(Document.deleted_at.is_(None))
        .group_by(Document.doc_type)
        .all()
    )
    documents_by_type = {str(row[0].value if hasattr(row[0], "value") else row[0]): row[1] for row in type_rows}

    lang_rows = (
        db.query(DocumentChunk.language, func.count(DocumentChunk.id))
        .filter(DocumentChunk.language.isnot(None))
        .group_by(DocumentChunk.language)
        .all()
    )
    chunks_by_language = {str(row[0]): row[1] for row in lang_rows}

    total_chunks = db.query(DocumentChunk).count()
    total_docs = db.query(Document).filter(Document.deleted_at.is_(None)).count()
    avg_chunks = total_chunks / max(total_docs, 1)

    edge_rows = db.query(GraphEdge.edge_type, func.count(GraphEdge.id)).group_by(GraphEdge.edge_type).all()
    graph_edge_types = {str(row[0]): row[1] for row in edge_rows}

    return KnowledgeStats(
        documents_by_type=documents_by_type,
        chunks_by_language=chunks_by_language,
        avg_chunks_per_document=round(avg_chunks, 1),
        graph_edge_types=graph_edge_types,
    )


class RetrievalMetricsResponse(BaseModel):
    total_searches: int
    avg_results: float
    avg_latency_ms: float
    avg_top_score: float
    zero_result_rate: float


@router.get("/knowledge/retrieval-metrics", response_model=RetrievalMetricsResponse)
async def retrieval_metrics(
    _user: Any = Depends(get_current_user),
):
    return get_retrieval_metrics().get_stats()
