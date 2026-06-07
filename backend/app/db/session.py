from __future__ import annotations

from backend.app.db.bootstrap import (
    bootstrap_database,
    get_database_url as _get_database_url,
    get_engine as _get_engine,
    get_session_factory,
    reset_engine as _reset_engine,
)


def get_engine():
    return _get_engine()


def get_database_url():
    return _get_database_url()


def reset_db_engine():
    _reset_engine()


class DynamicSessionLocal:
    def __call__(self, *args, **kwargs):
        session_factory = get_session_factory()
        return session_factory(*args, **kwargs)

    def configure(self, **kwargs):
        session_factory = get_session_factory()
        session_factory.configure(**kwargs)


SessionLocal = DynamicSessionLocal()
