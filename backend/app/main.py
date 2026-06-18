"""
Entrypoint for the FastAPI app — Auth + Memory only.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when running this file directly.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.memory import router as memory_router
from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.logging import get_logger, setup_logging
from backend.app.core.middleware import RequestLoggingMiddleware
from backend.app.core.system_paths import ensure_system_dirs
from backend.app.db.bootstrap import bootstrap_database

setup_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} started")

    ensure_system_dirs()
    bootstrap_database()

    # Test Redis connectivity (optional — fails open)
    from backend.app.core.redis import redis_cache
    await redis_cache.ping()

    try:
        from backend.app.db import session as db_session
        db_session.get_engine()
        logger.info("System database initialized at %s", db_session.get_database_url())
    except Exception as e:
        logger.error("Failed to initialize system database on startup: %s", e)

    yield

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
app.include_router(auth_router)
app.include_router(memory_router)

@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} is running 🚀"
    }
