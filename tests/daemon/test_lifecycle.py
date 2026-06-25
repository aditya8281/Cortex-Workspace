"""Tests for lifecycle manager."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.app.daemon.lifecycle import LifecycleHook, LifecycleManager, get_lifecycle, reset_lifecycle


class TestLifecycleManager:
    def setup_method(self):
        self.mgr = LifecycleManager()

    def test_initial_state(self):
        assert self.mgr.is_started is False
        assert self.mgr.is_shutting_down is False

    def test_register_hook(self):
        hook = LifecycleHook(name="test", callback=AsyncMock(), phase="post_start", order=100)
        self.mgr.register(hook)
        assert len(self.mgr._hooks) == 1

    def test_hooks_sorted_by_order(self):
        self.mgr.register(LifecycleHook(name="second", callback=AsyncMock(), phase="post_start", order=200))
        self.mgr.register(LifecycleHook(name="first", callback=AsyncMock(), phase="post_start", order=50))
        hooks = self.mgr._hooks_for_phase("post_start")
        assert hooks[0].name == "first"
        assert hooks[1].name == "second"

    async def test_run_startup(self):
        mock_hook = AsyncMock()
        self.mgr.register(LifecycleHook(name="test", callback=mock_hook, phase="post_start"))
        await self.mgr.run_startup()
        assert self.mgr.is_started is True
        mock_hook.assert_awaited_once()

    async def test_run_startup_pre_and_post(self):
        pre = AsyncMock()
        post = AsyncMock()
        self.mgr.register(LifecycleHook(name="pre", callback=pre, phase="pre_start"))
        self.mgr.register(LifecycleHook(name="post", callback=post, phase="post_start"))
        await self.mgr.run_startup()
        pre.assert_awaited_once()
        post.assert_awaited_once()

    async def test_run_shutdown(self):
        mock_hook = AsyncMock()
        self.mgr.register(LifecycleHook(name="test", callback=mock_hook, phase="pre_stop"))
        self.mgr._started = True
        await self.mgr.run_shutdown()
        assert self.mgr.is_started is False
        mock_hook.assert_awaited_once()

    async def test_shutdown_idempotent(self):
        mock_hook = AsyncMock()
        self.mgr.register(LifecycleHook(name="test", callback=mock_hook, phase="pre_stop"))
        await self.mgr.run_shutdown()
        await self.mgr.run_shutdown()  # Second call should be no-op
        mock_hook.assert_awaited_once()

    async def test_critical_hook_failure_propagates(self):
        async def fail():
            raise RuntimeError("critical failure")

        self.mgr.register(LifecycleHook(name="critical", callback=fail, phase="post_start", critical=True))
        with pytest.raises(RuntimeError, match="critical failure"):
            await self.mgr.run_startup()

    async def test_non_critical_hook_failure_logged(self):
        async def fail():
            raise RuntimeError("non-critical")

        ok_hook = AsyncMock()
        self.mgr.register(LifecycleHook(name="failing", callback=fail, phase="post_start", critical=False))
        self.mgr.register(LifecycleHook(name="ok", callback=ok_hook, phase="post_start"))
        await self.mgr.run_startup()
        # ok hook should still run after failing non-critical hook
        ok_hook.assert_awaited_once()

    def test_clear(self):
        self.mgr.register(LifecycleHook(name="test", callback=AsyncMock(), phase="post_start"))
        self.mgr._started = True
        self.mgr.clear()
        assert len(self.mgr._hooks) == 0
        assert self.mgr.is_started is False


class TestGetLifecycle:
    def test_singleton(self):
        reset_lifecycle()
        mgr1 = get_lifecycle()
        mgr2 = get_lifecycle()
        assert mgr1 is mgr2

    def test_reset(self):
        mgr1 = get_lifecycle()
        reset_lifecycle()
        mgr2 = get_lifecycle()
        assert mgr1 is not mgr2
