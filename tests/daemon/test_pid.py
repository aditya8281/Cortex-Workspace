"""Tests for PID file management."""

from __future__ import annotations

from unittest.mock import patch

import pytest

import backend.app.daemon.pid as pid_mod
from backend.app.daemon.pid import (
    PidFileError,
    assert_not_running,
    is_running,
    read_pid,
    remove_pid,
    write_pid,
)


@pytest.fixture(autouse=True)
def _temp_pid_dir(tmp_path):
    """Redirect PID directory to a temp path."""
    new_pid_dir = tmp_path / ".cortex"
    new_pid_dir.mkdir(parents=True, exist_ok=True)
    new_pid_file = new_pid_dir / "cortexd.pid"
    with (
        patch.object(pid_mod, "PID_DIR", new_pid_dir),
        patch.object(pid_mod, "PID_FILE", new_pid_file),
    ):
        yield
    if new_pid_file.exists():
        new_pid_file.unlink()
    if new_pid_dir.exists():
        new_pid_dir.rmdir()


class TestWritePid:
    def test_writes_pid_file(self):
        pid = write_pid(version="test")
        assert pid_mod.PID_FILE.exists()
        content = pid_mod.PID_FILE.read_text().strip()
        parts = content.split(",")
        assert parts[0] == str(pid)
        assert parts[2] == "test"

    def test_raises_if_alive(self):
        write_pid(version="test")
        with (
            patch("backend.app.daemon.pid._is_pid_alive", return_value=True),
            pytest.raises(PidFileError, match="already running"),
        ):
            write_pid(version="test")

    def test_cleans_up_stale_pid(self):
        write_pid(version="test")
        with patch("backend.app.daemon.pid._is_pid_alive", return_value=False):
            write_pid(version="test2")
        assert pid_mod.PID_FILE.exists()


class TestReadPid:
    def test_returns_none_when_no_file(self):
        assert read_pid() is None

    def test_returns_parsed_content(self):
        write_pid(version="test")
        info = read_pid()
        assert info is not None
        assert "pid" in info
        assert "start_time" in info
        assert info["version"] == "test"

    def test_handles_malformed_file(self):
        pid_mod.PID_FILE.write_text("not-a-number")
        assert read_pid() is None

    def test_handles_empty_file(self):
        pid_mod.PID_FILE.write_text("")
        assert read_pid() is None


class TestIsRunning:
    def test_returns_false_no_file(self):
        assert is_running() is False

    def test_returns_true_when_alive(self):
        write_pid(version="test")
        with patch("backend.app.daemon.pid._is_pid_alive", return_value=True):
            assert is_running() is True

    def test_returns_false_when_dead(self):
        write_pid(version="test")
        with patch("backend.app.daemon.pid._is_pid_alive", return_value=False):
            assert is_running() is False


class TestRemovePid:
    def test_removes_file(self):
        write_pid(version="test")
        remove_pid()
        assert not pid_mod.PID_FILE.exists()

    def test_no_error_if_missing(self):
        remove_pid()


class TestAssertNotRunning:
    def test_passes_when_no_file(self):
        assert_not_running()

    def test_raises_when_alive(self):
        write_pid(version="test")
        with (
            patch("backend.app.daemon.pid._is_pid_alive", return_value=True),
            pytest.raises(PidFileError, match="already running"),
        ):
            assert_not_running()
