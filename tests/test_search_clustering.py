"""Tests for SearchClusterer."""

import pytest

from backend.app.services.hybrid_retrieval import RetrievalResult
from backend.app.services.search_clustering import SearchClusterer, ResultCluster


@pytest.fixture()
def clusterer():
    return SearchClusterer()


def _make_result(file_path, score, content="content"):
    return RetrievalResult(content=content, source="vector", score=score, file_path=file_path)


def test_cluster_by_file(clusterer):
    results = [
        _make_result("a.py", 0.9),
        _make_result("a.py", 0.8),
        _make_result("b.py", 0.7),
    ]
    clusters = clusterer.cluster(results)
    assert len(clusters) == 2
    assert clusters[0].document_path == "a.py"
    assert clusters[0].result_count == 2


def test_cluster_empty(clusterer):
    clusters = clusterer.cluster([])
    assert len(clusters) == 0


def test_cluster_best_score(clusterer):
    results = [
        _make_result("a.py", 0.5),
        _make_result("a.py", 0.9),
    ]
    clusters = clusterer.cluster(results)
    assert clusters[0].best_score == 0.9
    assert clusters[0].total_score == 1.4


def test_cluster_sorted_by_score(clusterer):
    results = [
        _make_result("b.py", 0.5),
        _make_result("a.py", 0.9),
    ]
    clusters = clusterer.cluster(results)
    assert clusters[0].document_path == "a.py"


def test_get_top_per_document(clusterer):
    results = [
        _make_result("a.py", 0.9, "first"),
        _make_result("a.py", 0.8, "second"),
        _make_result("a.py", 0.7, "third"),
        _make_result("a.py", 0.6, "fourth"),
    ]
    top = clusterer.get_top_per_document(results, max_per_doc=2)
    assert len(top) == 2
    assert top[0].content == "first"


def test_get_top_per_document_mixed(clusterer):
    results = [
        _make_result("a.py", 0.9),
        _make_result("b.py", 0.8),
        _make_result("a.py", 0.7),
        _make_result("b.py", 0.6),
    ]
    top = clusterer.get_top_per_document(results, max_per_doc=1)
    assert len(top) == 2
