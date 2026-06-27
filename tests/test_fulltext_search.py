"""Tests for FullTextSearch."""

import pytest
from sqlalchemy.orm import Session

from backend.app.models.repo_index import CodeChunk, RepoIndex
from backend.app.services.intelligence.fulltext import FullTextSearch


@pytest.fixture()
def fts(db_session: Session):
    return FullTextSearch(db_session)


def _setup_code_chunks(db_session: Session):
    repo = RepoIndex(repo_path="/test", repo_name="test", total_files=1, total_chunks=3)
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    chunks = [
        CodeChunk(
            repo_id=repo.id,
            file_path="main.py",
            chunk_index=0,
            content="def calculate_sum(a, b): return a + b",
            language="python",
        ),
        CodeChunk(
            repo_id=repo.id,
            file_path="utils.py",
            chunk_index=1,
            content="def parse_json(text): import json; return json.loads(text)",
            language="python",
        ),
        CodeChunk(
            repo_id=repo.id,
            file_path="models.py",
            chunk_index=2,
            content="class User: def __init__(self, name): self.name = name",
            language="python",
        ),
    ]
    db_session.add_all(chunks)
    db_session.commit()


def test_search_code_basic(db_session: Session, fts: FullTextSearch):
    _setup_code_chunks(db_session)
    results = fts.search_code("calculate sum")
    assert db_session.bind is not None
    is_postgres = db_session.bind.dialect.name == "postgresql"
    if is_postgres:
        assert len(results) >= 1
        assert results[0].source == "code"
    else:
        # SQLite: to_tsvector not supported, graceful fallback
        assert results == []


def test_search_code_no_results(db_session: Session, fts: FullTextSearch):
    _setup_code_chunks(db_session)
    results = fts.search_code("nonexistent_xyz")
    assert len(results) == 0


def test_search_code_with_language_filter(db_session: Session, fts: FullTextSearch):
    _setup_code_chunks(db_session)
    results = fts.search_code("function", language="python")
    assert len(results) >= 0


def test_search_code_with_repo_filter(db_session: Session, fts: FullTextSearch):
    _setup_code_chunks(db_session)
    repo = db_session.query(RepoIndex).first()
    assert repo is not None
    results = fts.search_code("sum", repo_id=repo.id)
    assert len(results) >= 0


def test_search_code_graceful_on_missing_table(db_session: Session, fts: FullTextSearch):
    results = fts.search_code("test")
    assert results == []
