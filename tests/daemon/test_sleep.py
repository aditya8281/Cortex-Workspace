"""Tests for sleep/wake lifecycle."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from backend.app.daemon.sleep import DaemonState, SleepManager


class TestSleepManager:
    def setup_method(self):
        self.mgr = SleepManager()

    def test_initial_state_active(self):
        assert self.mgr.state == DaemonState.ACTIVE
        assert self.mgr.is_sleeping is False

    def test_idle_seconds_starts_at_zero(self):
        assert self.mgr.idle_seconds < 1.0

    def test_record_activity_resets_idle(self):
        import time

        self.mgr._last_activity = time.time() - 100
        self.mgr.record_activity()
        assert self.mgr.idle_seconds < 1.0

    def test_record_activity_wakes_from_sleep(self):
        self.mgr._state = DaemonState.SLEEPING
        self.mgr._last_activity = 0
        # Patch create_task to avoid needing event loop
        with patch("asyncio.create_task") as mock_create:
            self.mgr.record_activity()
            mock_create.assert_called_once()
        assert self.mgr.idle_seconds < 1.0

    def test_reset_idle_timer(self):
        self.mgr._last_activity = 0
        self.mgr.reset_idle_timer()
        assert self.mgr.idle_seconds < 1.0

    def test_on_sleep_callback_registered(self):
        cb = AsyncMock()
        self.mgr.on_sleep(cb)
        assert cb in self.mgr._on_sleep_callbacks

    def test_on_wake_callback_registered(self):
        cb = AsyncMock()
        self.mgr.on_wake(cb)
        assert cb in self.mgr._on_wake_callbacks

    async def test_sleep_triggers_callbacks(self):
        cb = AsyncMock()
        self.mgr.on_sleep(cb)
        self.mgr._state = DaemonState.ACTIVE
        self.mgr._last_activity = 0

        await self.mgr._sleep()
        assert self.mgr.is_sleeping is True
        cb.assert_awaited_once()

    async def test_wake_triggers_callbacks(self):
        cb = AsyncMock()
        self.mgr.on_wake(cb)
        self.mgr._state = DaemonState.SLEEPING
        await self.mgr._wake()
        assert self.mgr.state == DaemonState.ACTIVE
        cb.assert_awaited_once()

    async def test_sleep_is_idempotent(self):
        self.mgr._state = DaemonState.SLEEPING
        await self.mgr._sleep()
        assert self.mgr.is_sleeping is True

    async def test_wake_is_idempotent(self):
        self.mgr._state = DaemonState.ACTIVE
        await self.mgr._wake()
        assert self.mgr.state == DaemonState.ACTIVE

    async def test_start_stop_loop(self):
        self.mgr.start()
        assert self.mgr._sleep_task is not None
        assert not self.mgr._sleep_task.done()

        await self.mgr.stop()
        assert self.mgr._sleep_task is None

    async def test_start_is_idempotent(self):
        self.mgr.start()
        task1 = self.mgr._sleep_task
        self.mgr.start()
        assert self.mgr._sleep_task is task1
        await self.mgr.stop()

    async def test_sleep_callback_error_logged(self, caplog):
        import logging

        caplog.set_level(logging.WARNING)

        async def failing_cb():
            raise RuntimeError("callback failed")

        self.mgr.on_sleep(failing_cb)
        self.mgr._state = DaemonState.ACTIVE
        self.mgr._last_activity = 0
        await self.mgr._sleep()
        assert "callback failed" in caplog.text
        assert self.mgr.is_sleeping is True
