"""
Entrypoint for the FastAPI app.

This module is safe to execute directly (``python3 backend/app/main.py``).
When executed as a script, Python's import path doesn't include the project
root, which causes imports like `backend.app...` to fail. We ensure the
project root is on `sys.path` early so imports work regardless of how the
module is executed.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when running this file directly.
# backend/app/main.py -> parents[2] == project root
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from contextlib import asynccontextmanager
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.router import api_router
from backend.app.api.chat import router as chat_router
from backend.app.api.auth import router as auth_router
from backend.app.api.memory import router as memory_router
from backend.app.api.system import router as system_router
from backend.app.api.models_control import router as models_control_router
from backend.app.api.vault import router as vault_router
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.core.middleware import RequestLoggingMiddleware
from backend.app.core.logging import get_logger
from backend.app.core.system_paths import ensure_system_dirs
from backend.app.db.bootstrap import bootstrap_database


setup_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} started")

    ensure_system_dirs()
    bootstrap_database()

    # Test Redis connectivity
    from backend.app.core.redis import redis_cache
    await redis_cache.ping()
    
    # Test Redis connectivity
    from backend.app.core.redis import redis_cache
    await redis_cache.ping()

    import asyncio
    try:
        from backend.app.db import session as db_session
        db_session.get_engine()
        logger.info("System database initialized at %s", db_session.get_database_url())
    except Exception as e:
        logger.error("Failed to initialize system database on startup: %s", e)

    def warmup_executor():
        try:
            logger.info("Starting background warmup: Loading AIExecutor...")
            from backend.app.executor import AIExecutor
            AIExecutor()
            logger.info("Background warmup complete: AIExecutor is ready.")
        except Exception as ex:
            logger.error(f"Error during background warmup: {ex}")

    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, warmup_executor)

    from backend.app.intelligence.observer_service import BackgroundObserverService
    from backend.app.ai.model_registry import ModelRegistry
    from backend.app.services.memory_manager import memory_manager

    observer = BackgroundObserverService(poll_interval_seconds=90)
    observer.start(loop=loop)
    memory_manager.register_service("observer", observer)
    logger.info("Cortex background observer started")

    async def warmup_ollama_inventory():
        try:
            logger.info("Starting background Ollama inventory warmup...")
            await ModelRegistry.prime_ollama_inventory_cache()
            logger.info("Background Ollama inventory warmup complete")
        except Exception as ex:
            logger.error("Error during Ollama inventory warmup: %s", ex)

    loop.create_task(warmup_ollama_inventory())

    yield

    observer.stop()
    await redis_cache.close()
    logger.info("Redis cache connection closed")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RequestLoggingMiddleware
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(memory_router)
app.include_router(system_router)
app.include_router(models_control_router)
app.include_router(vault_router)

@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} is running 🚀"
    }
