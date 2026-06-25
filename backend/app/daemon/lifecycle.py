"""Daemon lifecycle manager — startup/shutdown hooks, state flush."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from backend.app.core.logging import get_logger
from backend.app.daemon.pid import remove_pid

logger = get_logger(__name__)


@dataclass
class LifecycleHook:
    """A hook that runs at a specific lifecycle phase."""

    name: str
    callback: Callable[[], Awaitable[Any]]
    phase: str  # "pre_start", "post_start", "pre_stop", "post_stop"
    order: int = 100
    critical: bool = False


class LifecycleManager:
    """Manages daemon startup and shutdown hook execution.

    Usage:
        mgr = LifecycleManager()
        mgr.register(LifecycleHook("init_db", init_db, "post_start"))
        await mgr.run_startup()
        # ... run main loop ...
        await mgr.run_shutdown()
    """

    def __init__(self) -> None:
        self._hooks: list[LifecycleHook] = []
        self._started = False
        self._shutting_down = False

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def is_shutting_down(self) -> bool:
        return self._shutting_down

    def register(self, hook: LifecycleHook) -> None:
        """Register a lifecycle hook."""
        self._hooks.append(hook)

    def _hooks_for_phase(self, phase: str) -> list[LifecycleHook]:
        return sorted(
            (h for h in self._hooks if h.phase == phase),
            key=lambda h: h.order,
        )

    async def run_startup(self) -> None:
        """Run all post_start hooks in order. Called after server binds."""
        logger.info("Running startup hooks...")
        for hook in self._hooks_for_phase("pre_start"):
            await self._run_hook(hook)

        for hook in self._hooks_for_phase("post_start"):
            await self._run_hook(hook)

        self._started = True
        logger.info("Daemon startup complete")

    async def run_shutdown(self) -> None:
        """Run shutdown hooks in reverse order. Called on SIGTERM/SIGINT."""
        if self._shutting_down:
            return
        self._shutting_down = True
        logger.info("Running shutdown hooks...")

        for hook in reversed(self._hooks_for_phase("pre_stop")):
            await self._run_hook(hook)

        for hook in reversed(self._hooks_for_phase("post_stop")):
            await self._run_hook(hook)

        # Always clean up PID file
        remove_pid()
        self._started = False
        logger.info("Daemon shutdown complete")

    async def _run_hook(self, hook: LifecycleHook) -> None:
        """Execute a single hook with error handling."""
        try:
            await hook.callback()
            logger.debug("Lifecycle hook '%s' completed", hook.name)
        except Exception as exc:
            logger.error("Lifecycle hook '%s' failed: %s", hook.name, exc)
            if hook.critical:
                raise

    def clear(self) -> None:
        """Remove all hooks (for testing)."""
        self._hooks.clear()
        self._started = False
        self._shutting_down = False


# Module-level singleton
_lifecycle: LifecycleManager | None = None


def get_lifecycle() -> LifecycleManager:
    """Get or create the global LifecycleManager."""
    global _lifecycle
    if _lifecycle is None:
        _lifecycle = LifecycleManager()
    return _lifecycle


def reset_lifecycle() -> None:
    """Reset the global lifecycle (for testing)."""
    global _lifecycle
    _lifecycle = None
