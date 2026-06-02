import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.app.rag.embeddings import EmbeddingModel
from backend.app.rag.vector_store import VectorStore
from backend.app.rag.text_chunker import TextChunker
from backend.app.rag.retriever import RepoIndexBuilder
from backend.app.ai.ingestion.scanner import RepoScanner


@pytest.fixture(name="mock_sentence_transformer")
def fixture_mock_sentence_transformer():
    with patch("backend.app.rag.embeddings.SentenceTransformer") as mock_transformer:
        mock_instance = MagicMock()
        mock_instance.encode.side_effect = lambda texts: np.random.rand(len(texts), 384).tolist()
        mock_transformer.return_value = mock_instance
        yield mock_instance


def test_embedding_model(mock_sentence_transformer):
    embedder = EmbeddingModel()
    texts = ["hello", "world"]
    vectors = embedder.encode(texts)

    assert isinstance(vectors, np.ndarray)
    assert vectors.shape == (2, 384)
    assert vectors.dtype == np.float32


def test_vector_store():
    store = VectorStore(dim=4)
    vectors = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]], dtype="float32")
    meta = [{"name": "doc1"}, {"name": "doc2"}]

    store.add(vectors, meta)

    # Search with L2 distance matching doc1
    query = np.array([[1.0, 0.1, 0.0, 0.0]], dtype="float32")
    results = store.search(query, top_k=1)

    assert len(results) == 1
    assert results[0]["data"]["name"] == "doc1"
    assert results[0]["score"] < 0.1


def test_text_chunker():
    chunker = TextChunker(chunk_size=10, overlap=2)
    text = "abcdefghijkl"
    chunks = chunker.chunk(text)

    assert len(chunks) == 2
    assert chunks[0] == "abcdefghij"
    assert chunks[1] == "ijkl"


def test_repo_scanner_ignores_venv_and_hidden(tmp_path):
    repo_dir = tmp_path / "my_project"
    repo_dir.mkdir()

    (repo_dir / "main.py").write_text("print('hello')", encoding="utf-8")
    (repo_dir / "README.md").write_text("# My Project", encoding="utf-8")

    venv_dir = repo_dir / ".venv"
    venv_dir.mkdir()
    (venv_dir / "library.py").write_text("class Lib: pass", encoding="utf-8")

    git_dir = repo_dir / ".git"
    git_dir.mkdir()
    (git_dir / "config.txt").write_text("some git config", encoding="utf-8")

    scanner = RepoScanner()
    files = scanner.scan(str(repo_dir))

    rel_paths = [Path(f).relative_to(repo_dir).name for f in files]

    assert "main.py" in rel_paths
    assert "README.md" in rel_paths
    assert "library.py" not in rel_paths
    assert "config.txt" not in rel_paths


def test_repo_index_builder(tmp_path, mock_sentence_transformer):
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    (repo_dir / "app.py").write_text("def my_func(): pass", encoding="utf-8")

    builder = RepoIndexBuilder()
    with patch.object(RepoScanner, "scan", return_value=[str(repo_dir / "app.py")]):
        store = builder.build(str(repo_dir))

    assert store is not None
    assert store.dim == 384
    assert len(store.metadata) > 0
    assert "app.py" in store.metadata[0]["file"]
