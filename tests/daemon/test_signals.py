"""Tests for signal handlers and graceful shutdown."""

from __future__ import annotations

import signal
from unittest.mock import patch

import pytest

import backend.app.daemon.signals as sig_mod
from backend.app.daemon.signals import (
    ShutdownRequested,
    is_reload_requested,
    is_shutdown_requested,
    restore_signal_handlers,
    setup_signal_handlers,
    wait_for_shutdown,
)


class TestSignalHandlers:
    def test_setup_installs_handlers(self):
        with patch("signal.signal") as mock_signal:
            setup_signal_handlers()
            sigcalls = [c.args[0] for c in mock_signal.call_args_list]
            assert signal.SIGTERM in sigcalls
            assert signal.SIGINT in sigcalls

    def test_setup_restore_cycle(self):
        setup_signal_handlers()
        assert is_shutdown_requested() is False
        restore_signal_handlers()

    def test_shutdown_flag_clear_initially(self):
        assert is_shutdown_requested() is False

    def test_shutdown_flag_set_via_handler(self):
        sig_mod._handle_sigterm(signal.SIGTERM, None)
        assert is_shutdown_requested() is True
        sig_mod._shutdown_flag = False  # Reset

    def test_restore_without_setup(self):
        restore_signal_handlers()

    def test_second_signal_exits(self):
        sig_mod._shutdown_flag = True
        with pytest.raises(SystemExit):
            sig_mod._handle_sigterm(signal.SIGTERM, None)
        sig_mod._shutdown_flag = False


class TestReloadSignal:
    def test_reload_flag_on_sighup(self):
        if not hasattr(signal, "SIGHUP"):
            pytest.skip("SIGHUP not available")
        sig_mod._handle_sighup(signal.SIGHUP, None)
        assert is_reload_requested() is True
        sig_mod._reload_requested = False

    def test_clear_reload_flag(self):
        sig_mod._reload_requested = True
        sig_mod.clear_reload_flag()
        assert is_reload_requested() is False


class TestWaitForShutdown:
    async def test_raises_when_shutdown_signaled(self, monkeypatch):
        monkeypatch.setattr("backend.app.daemon.signals._shutdown_flag", True)
        with pytest.raises(ShutdownRequested):
            await wait_for_shutdown(timeout=0.1)

    async def test_loops_until_shutdown(self, monkeypatch):
        import asyncio

        monkeypatch.setattr("backend.app.daemon.signals._shutdown_flag", False)

        async def _set_flag_after_delay():
            await asyncio.sleep(0.05)
            monkeypatch.setattr("backend.app.daemon.signals._shutdown_flag", True)

        asyncio.create_task(_set_flag_after_delay())
        with pytest.raises(ShutdownRequested):
            await wait_for_shutdown(timeout=2.0)
