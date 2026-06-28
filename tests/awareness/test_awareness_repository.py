"""Tests for v1.04 P02 repository scanning service."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from backend.app.services.awareness.repo_scanner import RepositoryScannerService


class TestRepositoryScannerService:
    def test_scan_python_repo(self, db_session: Session, tmp_path: object) -> None:
        """Scanning a Python repo detects language and framework."""
        import pathlib
        p = pathlib.Path(str(tmp_path))
        (p / "requirements.txt").write_text("fastapi==0.100.0\nuvicorn==0.23.0")
        (p / "main.py").write_text("from fastapi import FastAPI")
        (p / "utils.py").write_text("def helper(): pass")

        service = RepositoryScannerService(db_session)
        repo = service.scan_repository(user_id=1, repo_path=str(p))

        assert repo.repo_name == p.name
        languages = json.loads(repo.languages) if repo.languages else {}
        assert languages.get("python", 0) >= 2
        assert repo.total_files >= 3

    def test_scan_node_repo(self, db_session: Session, tmp_path: object) -> None:
        """Scanning a Node.js repo detects TypeScript and next.js."""
        import pathlib
        p = pathlib.Path(str(tmp_path))
        (p / "package.json").write_text(json.dumps({
            "dependencies": {"react": "^18.0.0", "next": "^14.0.0"},
            "devDependencies": {"typescript": "^5.0.0"}
        }))
        (p / "next.config.js").write_text("module.exports = {}")
        (p / "app.tsx").write_text("export default function App() {}")

        service = RepositoryScannerService(db_session)
        repo = service.scan_repository(user_id=1, repo_path=str(p))

        assert repo.framework == "next.js"
        languages = json.loads(repo.languages) if repo.languages else {}
        assert "typescript" in languages

    def test_scan_rust_repo(self, db_session: Session, tmp_path: object) -> None:
        """Scanning a Rust repo detects Cargo dependencies."""
        import pathlib
        p = pathlib.Path(str(tmp_path))
        (p / "Cargo.toml").write_text(
            '[dependencies]\nserde = { version = "1.0", features = ["derive"] }\ntokio = { version = "1" }'
        )
        (p / "main.rs").write_text("fn main() {}")

        service = RepositoryScannerService(db_session)
        repo = service.scan_repository(user_id=1, repo_path=str(p))

        assert repo.framework == "rust"
        dependencies = json.loads(repo.dependencies) if repo.dependencies else []
        assert "serde" in dependencies

    def test_upsert_scan(self, db_session: Session, tmp_path: object) -> None:
        """Re-scanning updates the existing record (upsert)."""
        import pathlib
        p = pathlib.Path(str(tmp_path))
        (p / "main.py").write_text("print('v1')")

        service = RepositoryScannerService(db_session)
        repo1 = service.scan_repository(user_id=1, repo_path=str(p))
        first_id = repo1.id

        (p / "utils.py").write_text("def helper(): pass")
        repo2 = service.scan_repository(user_id=1, repo_path=str(p))

        assert repo2.id == first_id
        assert repo2.total_files == 2

    def test_git_info(self, db_session: Session, tmp_path: object) -> None:
        """Git branch and commit are detected when .git exists."""
        import pathlib
        import subprocess
        p = pathlib.Path(str(tmp_path))
        subprocess.run(["git", "init"], cwd=str(p), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(p), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(p), capture_output=True, check=True)
        (p / "main.py").write_text("print('hello')")
        subprocess.run(["git", "add", "."], cwd=str(p), capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=str(p), capture_output=True, check=True)

        service = RepositoryScannerService(db_session)
        repo = service.scan_repository(user_id=1, repo_path=str(p))

        assert repo.git_branch is not None
        assert repo.last_commit_hash is not None
        assert len(repo.last_commit_hash) == 40  # SHA-1

    def test_empty_repo(self, db_session: Session, tmp_path: object) -> None:
        """Scanning an empty directory creates a valid record."""
        import pathlib
        p = pathlib.Path(str(tmp_path))

        service = RepositoryScannerService(db_session)
        repo = service.scan_repository(user_id=1, repo_path=str(p))

        assert repo.total_files == 0
        assert repo.total_lines == 0
