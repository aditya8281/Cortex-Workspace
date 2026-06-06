import logging
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
import threading

from backend.app.core.paths import PROJECT_ROOT
from backend.app.core import storage

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None
_engine_lock = threading.Lock()

def get_database_url() -> str:
    # Prefer explicit DATABASE_URL in production; fall back to memory-local sqlite
    from backend.app.core.config import settings
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    db_path = storage.get_database_path()
    return f"sqlite:///{db_path}"

def get_engine():
    global _engine
    with _engine_lock:
        if _engine is None:
            url = get_database_url()
            logger.info("Initializing SQLite database engine at %s", url)
            
            # Check and run migrations on first connect
            db_file_path = storage.get_database_path()
            run_migrations(str(db_file_path))
            
            _engine = create_engine(
                url,
                connect_args={"check_same_thread": False, "timeout": 30}
            )

            # Ensure SQLite uses WAL mode and sane pragmas to reduce locking contention
            def _set_sqlite_pragma(dbapi_conn, connection_record):
                try:
                    cur = dbapi_conn.cursor()
                    cur.execute("PRAGMA journal_mode=WAL;")
                    cur.execute("PRAGMA synchronous=NORMAL;")
                    cur.execute("PRAGMA foreign_keys=ON;")
                    cur.close()
                except Exception:
                    pass

            event.listen(_engine, "connect", _set_sqlite_pragma)
        return _engine

def reset_db_engine():
    global _engine, _SessionLocal
    with _engine_lock:
        if _engine is not None:
            logger.info("Disposing active database connection engine pool.")
            _engine.dispose()
            _engine = None
        _SessionLocal = None

def run_migrations(db_path: str):
    """Programmatically runs Alembic migrations upgrade head on the target SQLite file."""
    try:
        # Ensure parent directory exists using safe abstraction
        from backend.app.core.runtime import get_runtime
        runtime = get_runtime()
        runtime.create_dir(str(Path(db_path).expanduser().resolve().parent))
        
        ini_path = str(PROJECT_ROOT / "alembic.ini")
        cfg = Config(ini_path)
        
        db_url = f"sqlite:///{db_path}"
        cfg.set_main_option("sqlalchemy.url", db_url)
        
        logger.info("Running Alembic migrations programmatically on %s", db_url)
        command.upgrade(cfg, "head")
        logger.info("Alembic migrations completed successfully.")
    except Exception as e:
        logger.error("Failed to run programmatic migrations: %s", e)

class DynamicSessionLocal:
    def __call__(self, *args, **kwargs):
        global _SessionLocal
        if _SessionLocal is None:
            engine = get_engine()
            with _engine_lock:
                if _SessionLocal is None:
                    _SessionLocal = sessionmaker(
                        autocommit=False,
                        autoflush=False,
                        bind=engine
                    )
        return _SessionLocal(*args, **kwargs)

    def configure(self, **kwargs):
        global _SessionLocal
        if _SessionLocal is None:
            engine = get_engine()
            with _engine_lock:
                if _SessionLocal is None:
                    _SessionLocal = sessionmaker(
                        autocommit=False,
                        autoflush=False,
                        bind=engine
                    )
        _SessionLocal.configure(**kwargs)

# SessionLocal is a proxy object callable
SessionLocal = DynamicSessionLocal()
