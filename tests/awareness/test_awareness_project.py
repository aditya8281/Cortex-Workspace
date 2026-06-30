"""Tests for v1.04 P03 project scanner service."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from backend.app.models.awareness.project_detector import ProjectIndex
from backend.app.services.awareness.project_scanner import ProjectScannerService


class TestProjectScannerService:
    def test_scan_python_project(self, db_session: Session, tmp_path: object) -> None:
        """Scanning a Python project detects type and features."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "requirements.txt").write_text("fastapi==0.100.0")
        (p / "pyproject.toml").write_text("[tool.pytest]\nasyncio_mode = 'auto'")
        (p / "tests").mkdir()
        (p / "tests" / "test_main.py").write_text("def test_pass(): assert True")

        service = ProjectScannerService(db_session)
        project = service.scan_project(user_id=1, project_path=str(p))

        assert project.project_type == "python"
        assert project.has_tests == 1
        config = json.loads(project.configuration) if project.configuration else {}
        assert config.get("test_framework") == "pytest"

    def test_scan_node_project(self, db_session: Session, tmp_path: object) -> None:
        """Scanning a Node.js project detects frameworks and features."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "package.json").write_text(json.dumps({"name": "my-app", "version": "1.0.0"}))
        (p / "next.config.js").write_text("module.exports = {}")
        (p / "Dockerfile").write_text("FROM node:18")
        (p / ".github").mkdir()
        (p / ".github" / "workflows").mkdir()

        service = ProjectScannerService(db_session)
        project = service.scan_project(user_id=1, project_path=str(p))

        assert project.project_type == "node"
        frameworks = json.loads(project.frameworks) if project.frameworks else []
        assert "next.js" in frameworks
        assert project.has_docker == 1
        assert project.has_ci == 1

    def test_scan_rust_project(self, db_session: Session, tmp_path: object) -> None:
        """Scanning a Rust project detects type."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "Cargo.toml").write_text('[package]\nname = "myapp"\nversion = "0.1.0"')
        (p / "src").mkdir()
        (p / "src" / "main.rs").write_text("fn main() {}")

        service = ProjectScannerService(db_session)
        project = service.scan_project(user_id=1, project_path=str(p))

        assert project.project_type == "rust"

    def test_scan_unknown_project(self, db_session: Session, tmp_path: object) -> None:
        """Scanning a project with no known indicators returns unknown."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "mystery.file").write_text("unknown")

        service = ProjectScannerService(db_session)
        project = service.scan_project(user_id=1, project_path=str(p))

        assert project.project_type == "unknown"

    def test_upsert_project(self, db_session: Session, tmp_path: object) -> None:
        """Re-scanning updates the existing record."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "requirements.txt").write_text("fastapi")

        service = ProjectScannerService(db_session)
        p1 = service.scan_project(user_id=1, project_path=str(p))
        first_id = p1.id

        (p / "Dockerfile").write_text("FROM python:3.12")
        p2 = service.scan_project(user_id=1, project_path=str(p))

        assert p2.id == first_id
        assert p2.has_docker == 1

    def test_detect_ci_indicators(self, db_session: Session, tmp_path: object) -> None:
        """CI detection finds GitHub Actions workflows."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "requirements.txt").write_text("flask")
        (p / ".github").mkdir()
        (p / ".github" / "workflows").mkdir()
        (p / ".github" / "workflows" / "ci.yml").write_text("name: CI")

        service = ProjectScannerService(db_session)
        project = service.scan_project(user_id=1, project_path=str(p))

        assert project.has_ci == 1

    def test_user_isolation(self, db_session: Session, tmp_path: object) -> None:
        """Project indices are isolated by user_id."""
        import pathlib

        p = pathlib.Path(str(tmp_path))
        (p / "requirements.txt").write_text("flask")

        service = ProjectScannerService(db_session)
        service.scan_project(user_id=1, project_path=str(p))
        service.scan_project(user_id=2, project_path=str(p))

        user1 = db_session.query(ProjectIndex).filter(ProjectIndex.user_id == 1).count()
        user2 = db_session.query(ProjectIndex).filter(ProjectIndex.user_id == 2).count()

        assert user1 == 1
        assert user2 == 1

    def test_empty_project(self, db_session: Session, tmp_path: object) -> None:
        """Scanning an empty directory creates a valid record."""
        import pathlib

        p = pathlib.Path(str(tmp_path))

        service = ProjectScannerService(db_session)
        project = service.scan_project(user_id=1, project_path=str(p))

        assert project.project_type == "unknown"
        assert project.has_tests == 0
        assert project.has_ci == 0
        assert project.has_docker == 0
