import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
import threading

from backend.app.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None
_engine_lock = threading.Lock()

def get_database_url() -> str:
    from backend.app.services.memory_manager import memory_manager
    db_path = memory_manager.get_path("metadata_db", "app.db")
    return f"sqlite:///{db_path}"

def get_engine():
    global _engine
    with _engine_lock:
        if _engine is None:
            url = get_database_url()
            logger.info("Initializing SQLite database engine at %s", url)
            
            # Check and run migrations on first connect
            from backend.app.services.memory_manager import memory_manager
            db_file_path = memory_manager.get_path("metadata_db", "app.db")
            run_migrations(str(db_file_path))
            
            _engine = create_engine(
                url,
                connect_args={"check_same_thread": False}
            )
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
        runtime.create_dir(db_path.rsplit('/', 1)[0] if '/' in db_path else '.')
        
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