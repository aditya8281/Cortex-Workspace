"""Sleep/wake lifecycle — idle detection, sleep mode, wake triggers."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum, auto

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class DaemonState(Enum):
    """Daemon power state."""

    ACTIVE = auto()
    IDLE = auto()
    SLEEPING = auto()


@dataclass
class SleepConfig:
    """Configuration for sleep/wake behavior."""

    idle_timeout_seconds: int = 900  # 15 minutes
    poll_interval_seconds: int = 30  # check idle every 30s


class SleepManager:
    """Manages daemon sleep/wake lifecycle.

    Sleep: pause background tasks, release non-essential connections, reduce logging.
    Wake: resume background tasks, reconnect, catch up on missed events.
    """

    def __init__(self, config: SleepConfig | None = None) -> None:
        self._config = config or SleepConfig()
        self._state = DaemonState.ACTIVE
        self._last_activity: float = time.time()
        self._on_sleep_callbacks: list = []
        self._on_wake_callbacks: list = []
        self._sleep_task: asyncio.Task | None = None

    @property
    def state(self) -> DaemonState:
        return self._state

    @property
    def is_sleeping(self) -> bool:
        return self._state == DaemonState.SLEEPING

    def record_activity(self) -> None:
        """Record that activity happened, resetting idle timer."""
        self._last_activity = time.time()
        if self._state == DaemonState.SLEEPING:
            logger.info("Activity detected — waking daemon")
            asyncio.create_task(self._wake())

    @property
    def idle_seconds(self) -> float:
        """Seconds since last recorded activity."""
        return time.time() - self._last_activity

    def on_sleep(self, callback) -> None:
        """Register a callback invoked when daemon sleeps.
        Callback signature: async callback() -> None
        """
        self._on_sleep_callbacks.append(callback)

    def on_wake(self, callback) -> None:
        """Register a callback invoked when daemon wakes.
        Callback signature: async callback() -> None
        """
        self._on_wake_callbacks.append(callback)

    async def _sleep(self) -> None:
        """Transition to sleep state."""
        if self._state == DaemonState.SLEEPING:
            return
        logger.info("Daemon entering sleep mode (idle for %ss)", self.idle_seconds)
        self._state = DaemonState.SLEEPING
        for cb in self._on_sleep_callbacks:
            try:
                await cb()
            except Exception as exc:
                logger.warning("Sleep callback failed: %s", exc)
        logger.info("Daemon is now sleeping")

    async def _wake(self) -> None:
        """Transition to active state."""
        if self._state != DaemonState.SLEEPING:
            return
        logger.info("Daemon waking up")
        self._state = DaemonState.ACTIVE
        for cb in self._on_wake_callbacks:
            try:
                await cb()
            except Exception as exc:
                logger.warning("Wake callback failed: %s", exc)
        logger.info("Daemon is now active")

    async def _idle_check_loop(self) -> None:
        """Periodically check if daemon should sleep."""
        while True:
            await asyncio.sleep(self._config.poll_interval_seconds)
            if self._state == DaemonState.ACTIVE and self.idle_seconds >= self._config.idle_timeout_seconds:
                await self._sleep()

    def start(self) -> None:
        """Start the idle detection loop."""
        if self._sleep_task is None or self._sleep_task.done():
            self._sleep_task = asyncio.create_task(self._idle_check_loop())
            logger.debug("Sleep manager idle check started")

    async def stop(self) -> None:
        """Stop the idle detection loop."""
        if self._sleep_task and not self._sleep_task.done():
            self._sleep_task.cancel()
            try:
                await self._sleep_task
            except asyncio.CancelledError:
                pass
        self._sleep_task = None

    def reset_idle_timer(self) -> None:
        """Reset the idle timer to now."""
        self._last_activity = time.time()
