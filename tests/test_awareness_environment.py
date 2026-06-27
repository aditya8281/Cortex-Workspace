"""Tests for v1.04 P03 environment scanner service."""

from __future__ import annotations

import os

from backend.app.services.awareness.env_scanner import EnvironmentScannerService


class TestEnvironmentScannerService:
    def test_get_safe_environment(self) -> None:
        """Only safe variables are returned — no secrets."""
        service = EnvironmentScannerService()
        env = service.get_environment(user_id=1)

        for key in env:
            assert "SECRET" not in key.upper()
            assert "PASSWORD" not in key.upper()
            assert "TOKEN" not in key.upper()
            assert "API_KEY" not in key.upper()
            assert "DATABASE_URL" not in key.upper()

    def test_get_system_paths(self) -> None:
        """System paths are returned with expected keys."""
        service = EnvironmentScannerService()
        paths = service.get_system_paths()

        assert "home" in paths
        assert paths["home"].startswith("/")

    def test_safe_env_check_returns_list(self) -> None:
        """Safe env check returns list of dicts with name and is_set."""
        service = EnvironmentScannerService()
        checks = service.get_safe_env_check()

        assert isinstance(checks, list)
        assert len(checks) > 0
        for item in checks:
            assert "name" in item
            assert "is_set" in item
            assert isinstance(item["is_set"], bool)

    def test_home_env_var_always_present(self) -> None:
        """HOME is always in the safe allowlist."""
        service = EnvironmentScannerService()
        env = service.get_environment(user_id=1)

        if os.environ.get("HOME"):
            assert "HOME" in env

    def test_no_blacklisted_patterns_in_output(self) -> None:
        """No variable names matching secret patterns are ever returned."""
        from backend.app.services.awareness.env_scanner import SECRET_PATTERNS

        service = EnvironmentScannerService()
        env = service.get_environment(user_id=1)

        for key in env:
            for pattern in SECRET_PATTERNS:
                assert pattern not in key.upper(), f"Secret pattern '{pattern}' found in key '{key}'"
