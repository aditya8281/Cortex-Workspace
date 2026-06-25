"""Graceful signal handlers: SIGTERM, SIGINT, SIGHUP."""

from __future__ import annotations

import asyncio
import signal
from types import FrameType

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class ShutdownRequested(Exception):
    """Raised inside the event loop when a shutdown signal is received."""


_shutdown_flag: bool = False
_reload_requested: bool = False
_original_handlers: dict[int, signal._HANDLER | int | None] = {}


def is_shutdown_requested() -> bool:
    """Check if a shutdown signal has been received."""
    return _shutdown_flag


def is_reload_requested() -> bool:
    """Check if a reload (SIGHUP) has been requested."""
    return _reload_requested


def clear_reload_flag() -> None:
    """Clear the reload flag after handling."""
    global _reload_requested
    _reload_requested = False


def _handle_sigterm(sig: int, frame: FrameType | None) -> None:
    """Handle SIGTERM/SIGINT by setting shutdown flag."""
    global _shutdown_flag
    if _shutdown_flag:
        # Second signal — force exit
        logger.warning("Forced exit on second signal")
        raise SystemExit(1)
    _shutdown_flag = True
    logger.info("Shutdown signal received (signal %s). Draining in-flight...", sig)


def _handle_sighup(sig: int, frame: FrameType | None) -> None:
    """Handle SIGHUP by setting reload flag."""
    global _reload_requested
    _reload_requested = True
    logger.info("Reload signal (SIGHUP) received. Re-reading configuration...")


def setup_signal_handlers() -> None:
    """Install signal handlers for graceful shutdown and reload.

    Must be called from the main thread.
    """
    global _original_handlers
    signals = {
        signal.SIGTERM: _handle_sigterm,
        signal.SIGINT: _handle_sigterm,
    }
    # SIGHUP is Unix-only
    if hasattr(signal, "SIGHUP"):
        signals[signal.SIGHUP] = _handle_sighup

    for sig, handler in signals.items():
        _original_handlers[sig] = signal.getsignal(sig)
        signal.signal(sig, handler)

    logger.debug("Signal handlers installed: %s", list(signals.keys()))


def restore_signal_handlers() -> None:
    """Restore original signal handlers. Used during shutdown cleanup."""
    for sig, handler in _original_handlers.items():
        try:
            signal.signal(sig, handler)
        except (ValueError, OSError):
            pass
    _original_handlers.clear()
    logger.debug("Signal handlers restored")


async def wait_for_shutdown(timeout: float = 30.0) -> None:
    """Wait for shutdown signal, then drain for up to `timeout` seconds.

    Raises ShutdownRequested when a signal is received.
    """
    while not _shutdown_flag:
        await asyncio.sleep(0.5)
    raise ShutdownRequested("Shutdown signal received")
