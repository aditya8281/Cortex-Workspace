"""PID file management: create, read, validate, cleanup stale PIDs."""

from __future__ import annotations

import os
import time
from pathlib import Path

from backend.app.core.logging import get_logger

logger = get_logger(__name__)

PID_DIR = Path.home() / ".cortex"
PID_FILE = PID_DIR / "cortexd.pid"

# Expected format: "pid,start_timestamp,version\n"
PID_FILE_VERSION = "1"


class PidFileError(Exception):
    """Raised when PID file operations fail."""


def _ensure_pid_dir() -> None:
    PID_DIR.mkdir(parents=True, exist_ok=True)


def write_pid(version: str = "0.1.0") -> int:
    """Write current PID to PID_FILE. Returns PID written.

    Raises PidFileError if daemon is already running (non-stale PID).
    """
    _ensure_pid_dir()
    current_pid = os.getpid()

    if PID_FILE.exists():
        existing = _read_pid_file_raw()
        if existing and _is_pid_alive(existing["pid"]):
            raise PidFileError(
                f"Daemon already running (PID {existing['pid']}, started "
                f"{existing['start_time']}). Use 'cortexd stop' first."
            )
        # Stale PID — clean up
        logger.warning("Stale PID file found (PID %s). Cleaning up.", existing["pid"] if existing else "unknown")
        PID_FILE.unlink(missing_ok=True)

    content = f"{current_pid},{int(time.time())},{version}\n"
    PID_FILE.write_text(content)
    logger.debug("PID file written: PID %s", current_pid)
    return current_pid


def read_pid() -> dict | None:
    """Read PID file and return dict with pid, start_time, version, or None."""
    return _read_pid_file_raw()


def _read_pid_file_raw() -> dict | None:
    """Read and parse PID file."""
    if not PID_FILE.exists():
        return None
    try:
        raw = PID_FILE.read_text().strip()
        parts = raw.split(",", 2)
        if len(parts) < 2:
            logger.warning("Malformed PID file: %s", raw)
            return None
        result: dict = {
            "pid": int(parts[0]),
            "start_time": float(parts[1]),
        }
        if len(parts) >= 3:
            result["version"] = parts[2]
        return result
    except (OSError, ValueError, IndexError) as exc:
        logger.warning("Failed to read PID file: %s", exc)
        return None


def _is_pid_alive(pid: int) -> bool:
    """Check if a process with the given PID exists on this system."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we can't signal it — treat as alive
        return True
    except OSError:
        return False


def remove_pid() -> None:
    """Remove PID file if it exists. Logs but does not raise on failure."""
    try:
        PID_FILE.unlink(missing_ok=True)
        logger.debug("PID file removed")
    except OSError as exc:
        logger.warning("Failed to remove PID file: %s", exc)


def is_running() -> bool:
    """Check if daemon appears to be running (PID file exists + process alive)."""
    info = read_pid()
    if info is None:
        return False
    return _is_pid_alive(info["pid"])


def assert_not_running() -> None:
    """Raise PidFileError if daemon is already running."""
    info = read_pid()
    if info is None:
        return
    if _is_pid_alive(info["pid"]):
        raise PidFileError(
            f"Daemon already running (PID {info['pid']}). Use 'cortexd stop' or 'cortexd restart' first."
        )
    # Stale — clean up
    logger.warning("Removing stale PID %s", info["pid"])
    PID_FILE.unlink(missing_ok=True)
