"""Tests for v1.04 P02 filesystem indexing and change detection services."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models.awareness.file_tracker import FileIndex
from backend.app.services.awareness.file_indexer import FilesystemIndexerService


class TestFilesystemIndexerService:
    def test_scan_directory(self, db_session: Session, tmp_path: object) -> None:
        """Scanning a directory indexes all files."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "test.py").write_text("print('hello')")
        (p / "test.js").write_text("console.log('hello')")

        service = FilesystemIndexerService(db_session)
        files, stats = service.scan_directory(user_id=1, directory=str(p))

        assert len(files) == 2
        assert stats["created"] == 2

    def test_scan_skips_git_directory(self, db_session: Session, tmp_path: object) -> None:
        """The .git directory is skipped during scanning."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / ".git").mkdir()
        (p / ".git" / "config").write_text("git config")
        (p / "main.py").write_text("print('main')")

        service = FilesystemIndexerService(db_session)
        files, _ = service.scan_directory(user_id=1, directory=str(p))

        assert len(files) == 1
        assert files[0].file_name == "main.py"

    def test_scan_skips_common_dirs(self, db_session: Session, tmp_path: object) -> None:
        """node_modules, __pycache__, venv, .venv are skipped."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "node_modules").mkdir()
        (p / "node_modules" / "dep.js").write_text("module.exports={}")
        (p / "__pycache__").mkdir()
        (p / "__pycache__" / "mod.cpython-312.pyc").write_bytes(b"\x00")
        (p / "src").mkdir()
        (p / "src" / "main.py").write_text("print('ok')")

        service = FilesystemIndexerService(db_session)
        files, _ = service.scan_directory(user_id=1, directory=str(p))

        assert len(files) == 1
        assert files[0].file_name == "main.py"

    def test_content_hash(self, db_session: Session, tmp_path: object) -> None:
        """File index includes SHA-256 content hash."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "a.txt").write_text("content A")

        service = FilesystemIndexerService(db_session)
        files, _ = service.scan_directory(user_id=1, directory=str(p))

        assert len(files) == 1
        assert files[0].content_hash is not None
        assert len(files[0].content_hash) == 64  # SHA-256 hex digest

    def test_detect_changes_created(self, db_session: Session, tmp_path: object) -> None:
        """New files are detected as created."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "existing.py").write_text("original")

        service = FilesystemIndexerService(db_session)
        service.scan_directory(user_id=1, directory=str(p))

        (p / "new.py").write_text("new file")
        changes = service.detect_changes(user_id=1, directory=str(p))

        assert len(changes["created"]) == 1
        assert changes["created"][0].file_name == "new.py"

    def test_detect_changes_modified(self, db_session: Session, tmp_path: object) -> None:
        """Content changes are detected as modified."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        filepath = p / "a.py"
        filepath.write_text("version 1")

        service = FilesystemIndexerService(db_session)
        service.scan_directory(user_id=1, directory=str(p))

        filepath.write_text("version 2")
        changes = service.detect_changes(user_id=1, directory=str(p))

        assert len(changes["modified"]) == 1
        assert changes["modified"][0].content_hash != ""

    def test_detect_changes_deleted(self, db_session: Session, tmp_path: object) -> None:
        """Deleted files are detected."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "keep.py").write_text("keep")
        (p / "remove.py").write_text("remove")

        service = FilesystemIndexerService(db_session)
        service.scan_directory(user_id=1, directory=str(p))

        (p / "remove.py").unlink()
        changes = service.detect_changes(user_id=1, directory=str(p))

        assert any(d.endswith("/remove.py") for d in changes["deleted"])

    def test_idempotent_scan(self, db_session: Session, tmp_path: object) -> None:
        """Scanning the same file twice does not duplicate entries."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "test.py").write_text("print('hello')")

        service = FilesystemIndexerService(db_session)
        files1, _ = service.scan_directory(user_id=1, directory=str(p))
        files2, _ = service.scan_directory(user_id=1, directory=str(p))

        assert len(files1) == 1
        assert len(files2) == 1
        assert files1[0].id == files2[0].id

    def test_user_isolation(self, db_session: Session, tmp_path: object) -> None:
        """File indices are isolated by user_id."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "shared.py").write_text("shared content")

        service = FilesystemIndexerService(db_session)
        service.scan_directory(user_id=1, directory=str(p))
        service.scan_directory(user_id=2, directory=str(p))

        user1 = db_session.query(FileIndex).filter(FileIndex.user_id == 1).count()
        user2 = db_session.query(FileIndex).filter(FileIndex.user_id == 2).count()

        assert user1 == 1
        assert user2 == 1

    def test_directory_summary(self, db_session: Session, tmp_path: object) -> None:
        """Directory summary returns file counts and extensions."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "a.py").write_text("print('a')")
        (p / "b.py").write_text("print('b')")
        (p / "c.js").write_text("console.log('c')")

        service = FilesystemIndexerService(db_session)
        service.scan_directory(user_id=1, directory=str(p))
        summary = service.get_directory_summary(user_id=1, directory=str(p))

        assert summary["total_files"] == 3
        assert ".py" in summary["extensions"]
        assert summary["extensions"][".py"] == 2

    def test_empty_directory(self, db_session: Session, tmp_path: object) -> None:
        """Scanning an empty directory returns no files."""
        import pathlib

        p = pathlib.Path(str(tmp_path))

        service = FilesystemIndexerService(db_session)
        files, stats = service.scan_directory(user_id=1, directory=str(p))

        assert len(files) == 0
        assert stats["created"] == 0
