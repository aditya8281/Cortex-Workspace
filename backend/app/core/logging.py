import contextvars
import logging
import sys
from collections import deque
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any

LOG_BUFFER: deque[dict[str, Any]] = deque(maxlen=500)

_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    """Injects ``request_id`` into every log record when set on the current context.

    Usage:
        import logging
        logger = logging.getLogger(__name__)
        logger.addFilter(RequestIdFilter())
        # Then at request scope:
        RequestIdFilter.set("req-123")
        logger.info("hello")  # includes request_id=req-123
    """

    @classmethod
    def set(cls, request_id: str) -> None:
        _request_id_var.set(request_id)

    @classmethod
    def get(cls) -> str:
        return _request_id_var.get()

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


def setup_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": ("%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s")}
            },
            "filters": {
                "request_id": {
                    "()": RequestIdFilter,
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["request_id"],
                    "stream": sys.stdout,
                }
            },
            "root": {
                "handlers": ["console"],
                "level": "INFO",
            },
        }
    )

    root_logger = logging.getLogger()
    root_logger.addFilter(RequestIdFilter())
    if not any(isinstance(handler, BufferedLogHandler) for handler in root_logger.handlers):
        buffer_handler = BufferedLogHandler()
        buffer_handler.setLevel(logging.INFO)
        root_logger.addHandler(buffer_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_recent_logs(limit: int = 80) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 200))
    return list(LOG_BUFFER)[-safe_limit:]
