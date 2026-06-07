from __future__ import annotations

import logging
import threading
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.core.paths import PROJECT_ROOT
from backend.app.core.system_paths import ensure_system_dirs
from backend.app.core.storage_abstraction import get_system_storage

logger = logging.getLogger(__name__)

_engine = None
_session_factory = None
_bootstrap_lock = threading.Lock()


def get_database_path() -> Path:
    return get_system_storage().database_path


def get_database_url() -> str:
    return f"sqlite:///{get_database_path()}"




def ensure_database_file() -> Path:
    ensure_system_dirs()
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        return db_path

    return db_path


def run_migrations() -> None:
    db_path = ensure_database_file()
    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    logger.info("Running Alembic migrations against %s", db_path)
    command.upgrade(cfg, "head")


def _create_engine():
    global _engine
    if _engine is not None:
        return _engine

    db_path = ensure_database_file()
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    def _set_sqlite_pragma(dbapi_conn, connection_record):
        try:
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA synchronous=NORMAL;")
            cur.execute("PRAGMA foreign_keys=ON;")
            cur.close()
        except Exception:
            pass

    event.listen(engine, "connect", _set_sqlite_pragma)
    _engine = engine
    return engine


def bootstrap_database() -> None:
    with _bootstrap_lock:
        ensure_system_dirs()
        ensure_database_file()
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
                bind=get_engine(),
            )
        return _session_factory


def reset_engine() -> None:
    global _engine, _session_factory
    with _bootstrap_lock:
        if _engine is not None:
            _engine.dispose()
        _engine = None
        _session_factory = None

