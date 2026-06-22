"""Database bootstrapping — PostgreSQL.

Creates the SQLAlchemy engine and session factory using the DATABASE_URL
from application settings.  All SQLite-specific logic has been removed.
"""

from __future__ import annotations

import logging
import threading

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings
from backend.app.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

_engine = None
_session_factory = None
_bootstrap_lock = threading.RLock()


def get_database_url() -> str:
    """Return the PostgreSQL connection URL from settings."""
    url = settings.DATABASE_URL
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set.  "
            "Configure it in your .env file, e.g.:\n"
            "  DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex"
        )
    return url


def run_migrations() -> None:
    """Run Alembic migrations against the configured database."""
    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", get_database_url())
    logger.info("Running Alembic migrations")
    command.upgrade(cfg, "head")


def _create_engine():
    global _engine
    if _engine is not None:
        return _engine

    engine = create_engine(
        get_database_url(),
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_timeout=30,
        pool_recycle=3600,
        # Production recommendations (uncomment for production deployments):
        # pool_size=10,
        # max_overflow=20,
        # pool_timeout=60,
        # pool_recycle=1800,
        # pool_pre_ping=True,
    )
    _engine = engine
    return engine


def bootstrap_database() -> None:
    """Run migrations, then create the engine and session factory.

    Note: ``ensure_system_dirs()`` is not called here because PostgreSQL
    manages its own storage.  System directories (CortexMemory/) are
    created on-demand when vault / memory services need them.
    """
    with _bootstrap_lock:
        run_migrations()
        _create_engine()


def get_engine():
    with _bootstrap_lock:
        return _create_engine()


def get_session_factory():
    global _session_factory
    with _bootstrap_lock:
        if _session_factory is None:
            _session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=_create_engine(),
            )
        return _session_factory


def reset_engine() -> None:
    global _engine, _session_factory
    with _bootstrap_lock:
        if _engine is not None:
            _engine.dispose()
        _engine = None
        _session_factory = None
