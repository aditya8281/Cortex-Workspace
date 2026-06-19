"""Tests for Repository Scanner."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.models.repo_index import CodeChunk, RepoIndex  # noqa: F401
from backend.app.services.chunker import Chunk, chunk_code, chunk_text, detect_language
from backend.app.services.repo_scanner import RepoScanner


@pytest.fixture
def db_session():
    """Create isolated SQLite session per test."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


class TestDetectLanguage:
    def test_known_extensions(self):
        cases = [
            ("main.py", "python"),
            ("app.js", "javascript"),
            ("component.ts", "typescript"),
            ("page.tsx", "tsx"),
            ("button.jsx", "jsx"),
            ("lib.rs", "rust"),
            ("main.go", "go"),
            ("App.java", "java"),
            ("util.c", "c"),
            ("util.cpp", "cpp"),
            ("header.h", "c"),
            ("script.rb", "ruby"),
            ("index.php", "php"),
            ("main.swift", "swift"),
            ("app.kt", "kotlin"),
            ("query.sql", "sql"),
            ("build.sh", "shell"),
            ("readme.md", "markdown"),
            ("data.json", "json"),
            ("config.yaml", "yaml"),
            ("config.yml", "yaml"),
            ("Cargo.toml", "toml"),
            ("pom.xml", "xml"),
            ("index.html", "html"),
            ("styles.css", "css"),
        ]
        for file_path, expected in cases:
            assert detect_language(file_path) == expected, f"Failed for {file_path}"

    def test_unknown_extension(self):
        assert detect_language("file.xyz") is None

    def test_no_extension(self):
        assert detect_language("Makefile") is None

    def test_uppercase_extension(self):
        assert detect_language("main.PY") == "python"


class TestChunkCode:
    def test_single_function(self):
        content = "def foo():\n    pass\n"
        chunks = chunk_code(content, "test.py")
        assert len(chunks) >= 1
        assert chunks[0].symbol_name == "foo"

    def test_multiple_functions(self):
        content = (
            "def foo():\n    pass\n\n" + "def bar():\n    pass\n\n" + "def baz():\n    pass\n"
        )
        chunks = chunk_code(content, "test.py", max_tokens=10)
        assert len(chunks) >= 3

    def test_class_detection(self):
        content = "class MyClass:\n    def method(self):\n        pass\n"
        chunks = chunk_code(content, "test.py")
        assert chunks[0].symbol_name == "MyClass"
        assert chunks[0].symbol_type == "class"

    def test_javascript_function(self):
        content = "function hello() {\n  return 1;\n}\n"
        chunks = chunk_code(content, "test.js")
        assert chunks[0].symbol_name == "hello"

    def test_rust_function(self):
        content = "fn main() {\n    println!(\"hi\");\n}\n"
        chunks = chunk_code(content, "main.rs")
        assert chunks[0].symbol_name == "main"

    def test_empty_content(self):
        chunks = chunk_code("", "empty.py")
        assert chunks == []


class TestChunkText:
    def test_paragraphs(self):
        content = "Para one.\n\nPara two.\n\nPara three."
        chunks = chunk_text(content, "doc.md", max_tokens=2)
        assert len(chunks) == 3

    def test_single_paragraph(self):
        chunks = chunk_text("Just one paragraph.", "doc.md")
        assert len(chunks) == 1

    def test_empty_content(self):
        chunks = chunk_text("", "doc.md")
        assert chunks == []


class TestScanRepo:
    @patch("backend.app.services.repo_scanner.get_vector_db")
    @patch("backend.app.services.repo_scanner.get_embedding_service")
    def test_scan_python_repo(self, mock_get_emb, mock_get_vdb, db_session):
        """Test scanning a Python-only repository."""
        mock_emb = MagicMock()
        mock_emb.embed_batch.return_value = [[0.1] * 768]
        mock_emb.compute_embedding_id.return_value = "emb_test"
        mock_get_emb.return_value = mock_emb
        mock_get_vdb.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "main.py").write_text("def hello():\n    print('hi')\n")
            (tmp / "utils.py").write_text("class Util:\n    pass\n")

            scanner = RepoScanner(db_session)
            result = scanner.scan_repo(str(tmp))

            assert result.files_scanned == 2
            assert result.chunks_created >= 2
            assert "python" in result.languages
            assert result.languages["python"] == 2
            assert result.status == "completed"

    @patch("backend.app.services.repo_scanner.get_vector_db")
    @patch("backend.app.services.repo_scanner.get_embedding_service")
    def test_scan_mixed_repo(self, mock_get_emb, mock_get_vdb, db_session):
        """Test scanning a multi-language repo."""
        mock_emb = MagicMock()
        mock_emb.embed_batch.return_value = [[0.1] * 768]
        mock_emb.compute_embedding_id.return_value = "emb_test"
        mock_get_emb.return_value = mock_emb
        mock_get_vdb.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "main.py").write_text("x = 1\n")
            (tmp / "app.js").write_text("const a = 1;\n")
            (tmp / "readme.md").write_text("# Title\n\nContent here.\n")

            scanner = RepoScanner(db_session)
            result = scanner.scan_repo(str(tmp))

            assert result.files_scanned == 3
            assert "python" in result.languages
            assert "javascript" in result.languages
            assert "markdown" in result.languages

    @patch("backend.app.services.repo_scanner.get_vector_db")
    @patch("backend.app.services.repo_scanner.get_embedding_service")
    def test_scan_skips_dirs(self, mock_get_emb, mock_get_vdb, db_session):
        """Test that ignored directories are skipped."""
        mock_emb = MagicMock()
        mock_emb.embed_batch.return_value = [[0.1] * 768]
        mock_emb.compute_embedding_id.return_value = "emb_test"
        mock_get_emb.return_value = mock_emb
        mock_get_vdb.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "main.py").write_text("x = 1\n")
            node_modules = tmp / "node_modules"
            node_modules.mkdir()
            (node_modules / "lib.js").write_text("const lib = 1;\n")

            scanner = RepoScanner(db_session)
            result = scanner.scan_repo(str(tmp))

            assert result.files_scanned == 1
            assert "python" in result.languages

    def test_scan_nonexistent_path(self, db_session):
        """Test scanning a path that doesn't exist."""
        scanner = RepoScanner(db_session)
        with pytest.raises(ValueError, match="does not exist"):
            scanner.scan_repo("/nonexistent/path")


class TestGetRepoStatus:
    @patch("backend.app.services.repo_scanner.get_vector_db")
    @patch("backend.app.services.repo_scanner.get_embedding_service")
    def test_get_repo_status(self, mock_get_emb, mock_get_vdb, db_session):
        """Test getting repository status."""
        mock_emb = MagicMock()
        mock_emb.embed_batch.return_value = [[0.1] * 768]
        mock_emb.compute_embedding_id.return_value = "emb_test"
        mock_get_emb.return_value = mock_emb
        mock_get_vdb.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "main.py").write_text("def hello():\n    pass\n")

            scanner = RepoScanner(db_session)
            result = scanner.scan_repo(str(tmp))
            status = scanner.get_repo_status(result.repo_id)

            assert status is not None
            assert status.repo_name == tmp.name
            assert status.status == "completed"
            assert status.total_files == 1
            assert status.total_chunks >= 1

    def test_get_repo_status_missing(self, db_session):
        """Test getting status for non-existent repo."""
        scanner = RepoScanner(db_session)
        status = scanner.get_repo_status(999)
        assert status is None
