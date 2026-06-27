"""Tests for HybridRetrievalV2."""

import pytest
from sqlalchemy.orm import Session

from backend.app.services.intelligence.hybrid_retrieval import HybridRetrievalV2, RetrievalResult


@pytest.fixture()
def mock_retrieval(db_session: Session):
    mock_embedder = type(
        "Mock",
        (),
        {
            "embed_single": lambda s, t: [0.1] * 768,
        },
    )()
    mock_vdb = type(
        "Mock",
        (),
        {
            "search": lambda s, coll, q, limit=10, filter_payload=None: [],
        },
    )()
    mock_fts = type(
        "Mock",
        (),
        {
            "search_code": lambda s, q, repo_id=None, limit=20: [],
            "search_documents": lambda s, q, doc_type=None, limit=20: [],
        },
    )()
    return HybridRetrievalV2(db_session, embedding_service=mock_embedder, vector_db=mock_vdb, fulltext_search=mock_fts)


def test_rrf_merge(mock_retrieval: HybridRetrievalV2):
    results = {
        "vector": [
            RetrievalResult(content="a", source="vector", score=0.9, file_path="a.py"),
            RetrievalResult(content="b", source="vector", score=0.8, file_path="b.py"),
        ],
        "fulltext": [
            RetrievalResult(content="b", source="fulltext", score=0.7, file_path="b.py"),
            RetrievalResult(content="c", source="fulltext", score=0.6, file_path="c.py"),
        ],
    }
    merged = mock_retrieval._rrf_merge(results, 10)
    assert len(merged) == 3
    assert merged[0].content == "b"  # appears in both sources


def test_rrf_merge_single_source(mock_retrieval: HybridRetrievalV2):
    results = {
        "vector": [
            RetrievalResult(content="x", source="vector", score=0.9, file_path="x.py"),
        ],
    }
    merged = mock_retrieval._rrf_merge(results, 10)
    assert len(merged) == 1


def test_mmr_selects_diverse(mock_retrieval: HybridRetrievalV2):
    results = [
        RetrievalResult(content="python programming language", source="vector", score=0.9, file_path="a.py"),
        RetrievalResult(content="python programming tutorials", source="vector", score=0.85, file_path="b.py"),
        RetrievalResult(content="java programming language", source="vector", score=0.7, file_path="c.py"),
    ]
    diverse = mock_retrieval._mmr_rerank(results, 2, lambda_param=0.5)
    assert len(diverse) == 2


def test_text_similarity():
    assert HybridRetrievalV2._text_similarity("hello world", "hello world") == 1.0
    assert HybridRetrievalV2._text_similarity("hello", "world") == 0.0
    assert 0 < HybridRetrievalV2._text_similarity("hello world foo", "hello world bar") < 1.0


def test_result_key():
    r1 = RetrievalResult(content="x", source="vector", score=0.9, document_id=1)
    assert HybridRetrievalV2._result_key(r1) == "doc_1_"

    r2 = RetrievalResult(content="x", source="vector", score=0.9, file_path="a.py")
    assert HybridRetrievalV2._result_key(r2) == "file_a.py"


def test_retrieve_empty(mock_retrieval: HybridRetrievalV2):
    results = mock_retrieval.retrieve("test query")
    assert len(results) == 0


def test_retrieve_vector_source(mock_retrieval: HybridRetrievalV2):
    results = mock_retrieval.retrieve("test", sources=["vector"])
    assert len(results) == 0


def test_retrieve_fulltext_source(mock_retrieval: HybridRetrievalV2):
    results = mock_retrieval.retrieve("test", sources=["fulltext"])
    assert len(results) == 0
