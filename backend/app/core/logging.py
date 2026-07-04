"""Logging configuration for CORTEX.

Console (stdout) + rotating file + in-memory buffer.
File persists across restarts so /api/v1/system/logs shows history.
"""

from __future__ import annotations

import contextvars
import logging
import sys
from collections import deque
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

LOG_BUFFER: deque[dict[str, Any]] = deque(maxlen=2000)

_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


def set_request_id(request_id: str) -> None:
    """Set the request ID context variable for log correlation."""
    _request_id_var.set(request_id)


def get_request_id() -> str:
    """Get the current request ID from context."""
    return _request_id_var.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get() or "-"
        return True


class BufferedLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            LOG_BUFFER.append(
                {
                    "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                    "level": record.levelname.upper(),
                    "logger": record.name,
                    "message": record.getMessage(),
                    "request_id": getattr(record, "request_id", ""),
                    "module": record.module,
                    "pathname": record.pathname,
                    "lineno": record.lineno,
                }
            )
        except Exception:
            self.handleError(record)


_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s"
_initialized = False


def _load_log_file_into_buffer(log_path: str | Path) -> None:
    """Load recent log lines from file into the in-memory buffer after a restart."""
    filepath = Path(log_path)
    if not filepath.exists() or filepath.stat().st_size == 0:
        return
    try:
        text = filepath.read_text(encoding="utf-8")
        lines = text.strip().split("\n")
        for line in lines[-2000:]:
            if " | " not in line:
                continue
            parts = line.split(" | ", 4)
            if len(parts) == 5:
                LOG_BUFFER.append(
                    {
                        "timestamp": parts[0],
                        "level": parts[1],
                        "logger": parts[2],
                        "message": parts[4].strip(),
                        "request_id": parts[3].strip() if parts[3].strip() != "-" else "",
                        "module": "",
                        "pathname": "",
                        "lineno": 0,
                    }
                )
    except Exception:
        pass


def _resolve_log_file() -> Path:
    """Resolve log file path relative to project root."""
    from backend.app.core.config import settings

    log_path = settings.LOG_FILE_PATH
    log_file = Path(log_path)
    if not log_file.is_absolute():
        # Walk up from this file: backend/app/core/logging.py → project root
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        log_file = project_root / log_path
    log_file.parent.mkdir(parents=True, exist_ok=True)
    return log_file


def setup_logging(force: bool = False) -> None:
    """Configure logging once. Idempotent unless force=True.

    Call with force=True in the lifespan to re-apply after uvicorn overwrites handlers.
    """
    global _initialized
    if _initialized and not force:
        return
    if force:
        _initialized = False

    # Uvicorn's dictConfig(disable_existing_loggers=True) disables every logger
    # that exists at startup — including our middleware logger. Re-enable all
    # existing loggers so our root-level handlers see their records.
    if force:
        for name in list(logging.root.manager.loggerDict.keys()):
            logger_obj = logging.root.manager.loggerDict[name]
            if isinstance(logger_obj, logging.PlaceHolder):
                continue
            logger_obj.disabled = False
            logger_obj.propagate = True

    log_file = _resolve_log_file()
    formatter = logging.Formatter(_LOG_FORMAT)
    req_filter = RequestIdFilter()

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Rotating file handler
    try:
        fh = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setFormatter(formatter)
        fh.addFilter(req_filter)
        root.addHandler(fh)
    except Exception as e:
        print(f"[setup_logging] File handler error: {e}", file=sys.stderr)

    # In-memory buffer handler
    buf = BufferedLogHandler()
    buf.setLevel(logging.INFO)
    buf.setFormatter(formatter)
    buf.addFilter(req_filter)
    root.addHandler(buf)

    # Pre-load existing log file into buffer
    _load_log_file_into_buffer(log_file)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_recent_logs(limit: int = 80) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 200))
    return list(LOG_BUFFER)[-safe_limit:]
