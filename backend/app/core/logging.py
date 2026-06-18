import logging
import sys
from collections import deque
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any

LOG_BUFFER: deque[dict[str, Any]] = deque(maxlen=500)


class BufferedLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            LOG_BUFFER.append(
                {
                    "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                    "level": record.levelname.upper(),
                    "logger": record.name,
                    "message": record.getMessage(),
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
                "default": {
                    "format": (
                        "%(asctime)s | "
                        "%(levelname)s | "
                        "%(name)s | "
                        "%(message)s"
                    )
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
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
    if not any(isinstance(handler, BufferedLogHandler) for handler in root_logger.handlers):
        buffer_handler = BufferedLogHandler()
        buffer_handler.setLevel(logging.INFO)
        root_logger.addHandler(buffer_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_recent_logs(limit: int = 80) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 200))
    return list(LOG_BUFFER)[-safe_limit:]
