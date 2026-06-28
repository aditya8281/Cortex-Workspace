"""Integration tests for v1.04 P04 awareness API endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

AUTH_HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.fixture()
def auth_client(client: TestClient, mock_auth: MagicMock) -> TestClient:
    """Authenticated TestClient for awareness API tests."""
    return client


class TestAwarenessAPI:
    """Integration tests for the awareness REST API endpoints."""

    def test_get_device_info(self, auth_client: TestClient) -> None:
        """GET /device/info returns device data."""
        resp = auth_client.get("/api/v1/device/info", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "hostname" in data
        assert "os_type" in data
        assert data["os_type"] in ("linux", "darwin", "windows")

    def test_get_health(self, auth_client: TestClient) -> None:
        """GET /system-health returns health data."""
        resp = auth_client.get("/api/v1/system-health", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "services" in data
        assert "overall_status" in data

    def test_get_health_status(self, auth_client: TestClient) -> None:
        """GET /system-health/status returns summary."""
        resp = auth_client.get("/api/v1/system-health/status", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_status" in data
        assert data["overall_status"] in ("healthy", "degraded", "down", "unknown")

    def test_get_environment(self, auth_client: TestClient) -> None:
        """GET /environment returns only safe variables."""
        resp = auth_client.get("/api/v1/environment", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        for key in data:
            assert "SECRET" not in key.upper()
            assert "PASSWORD" not in key.upper()
            assert "TOKEN" not in key.upper()

    def test_get_system_paths(self, auth_client: TestClient) -> None:
        """GET /environment/paths returns paths."""
        resp = auth_client.get("/api/v1/environment/paths", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "home" in data

    def test_scan_directory(self, auth_client: TestClient, tmp_path: object) -> None:
        """POST /files/scan indexes files in directory."""
        import pathlib
        p = pathlib.Path(str(tmp_path))
        (p / "test.py").write_text("print('hello')")

        resp = auth_client.post(
            f"/api/v1/files/scan?directory={p}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["files_indexed"] >= 1

    def test_detect_changes(self, auth_client: TestClient, tmp_path: object) -> None:
        """GET /files/changes detects file changes."""
        import pathlib
        p = pathlib.Path(str(tmp_path))
        (p / "a.py").write_text("original")

        # First scan
        auth_client.post(f"/api/v1/files/scan?directory={p}", headers=AUTH_HEADERS)

        # Create new file
        (p / "b.py").write_text("new file")
        resp = auth_client.get(f"/api/v1/files/changes?directory={p}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] >= 1

    def test_directory_summary(self, auth_client: TestClient, tmp_path: object) -> None:
        """GET /files/summary returns file stats."""
        import pathlib
        p = pathlib.Path(str(tmp_path))
        (p / "a.py").write_text("print('a')")
        (p / "b.js").write_text("console.log('b')")

        auth_client.post(f"/api/v1/files/scan?directory={p}", headers=AUTH_HEADERS)
        resp = auth_client.get(f"/api/v1/files/summary?directory={p}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_files"] == 2

    def test_scan_repository(self, auth_client: TestClient, tmp_path: object) -> None:
        """POST /repository/scan indexes repository."""
        import pathlib
        p = pathlib.Path(str(tmp_path))
        (p / "requirements.txt").write_text("fastapi==0.100.0")
        (p / "main.py").write_text("from fastapi import FastAPI")

        resp = auth_client.post(
            f"/api/v1/repos/scan?repo_path={p}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "languages" in data
        assert "total_files" in data

    def test_scan_project(self, auth_client: TestClient, tmp_path: object) -> None:
        """GET /project/scan detects project type."""
        import pathlib
        p = pathlib.Path(str(tmp_path))
        (p / "requirements.txt").write_text("fastapi")
        (p / "tests").mkdir()

        resp = auth_client.get(
            f"/api/v1/project/scan?project_path={p}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_type"] == "python"

    def test_unauthenticated_returns_error(self, client: TestClient) -> None:
        """Unauthenticated requests fail (no dependency override)."""
        resp = client.get("/api/v1/device/info")
        assert resp.status_code in (401, 422, 500)

    def test_awareness_e2e(self, auth_client: TestClient, tmp_path: object) -> None:
        """End-to-end: scan → device → health → environment."""
        import pathlib
        p = pathlib.Path(str(tmp_path))
        (p / "main.py").write_text("print('hello')")

        # 1. Scan directory
        scan_resp = auth_client.post(
            f"/api/v1/files/scan?directory={p}",
            headers=AUTH_HEADERS,
        )
        assert scan_resp.status_code == 200

        # 2. Get device info
        device_resp = auth_client.get("/api/v1/device/info", headers=AUTH_HEADERS)
        assert device_resp.status_code == 200
        assert device_resp.json()["os_type"] is not None

        # 3. Get health
        health_resp = auth_client.get("/api/v1/system-health", headers=AUTH_HEADERS)
        assert health_resp.status_code == 200

        # 4. Get environment (safe)
        env_resp = auth_client.get("/api/v1/environment", headers=AUTH_HEADERS)
        assert env_resp.status_code == 200
        for key in env_resp.json():
            assert "SECRET" not in key.upper()
