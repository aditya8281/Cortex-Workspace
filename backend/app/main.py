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
from backend.app.api.v1.ws_system import router as ws_system_router
from backend.app.api.ws import router as ws_router
from backend.app.core.config import settings
from backend.app.core.csrf import setup_csrf_protection
from backend.app.core.https_redirect import setup_https_redirect
from backend.app.core.logging import get_logger, setup_logging
from backend.app.core.middleware import RequestLoggingMiddleware
from backend.app.core.rate_limit import setup_rate_limiting
from backend.app.core.system_paths import ensure_system_dirs
from backend.app.core.websocket import manager
from backend.app.db.bootstrap import bootstrap_database

setup_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} started")

    ensure_system_dirs()
    import sys

    if "pytest" not in sys.modules:
        bootstrap_database()

    # Test Redis connectivity (optional — fails open)
    from backend.app.core.redis import redis_cache

    await redis_cache.ping()

    # Initialize LLM manager
    from backend.app.services.llm.manager import llm_manager

    llm_manager.configure(
        llama_model_path=settings.LLM_MODEL_PATH or None,
        ollama_url=settings.OLLAMA_BASE_URL if settings.LLM_PROVIDER in ("auto", "ollama") else None,
        n_ctx=settings.LLM_CONTEXT_SIZE,
        n_gpu_layers=settings.LLM_GPU_LAYERS,
    )
    llm_status = await llm_manager.health_check()
    logger.info("LLM providers: %s", llm_status)

    try:
        await llm_manager.fetch_ollama_catalog()
        logger.info("Ollama model catalog cached on startup")
    except Exception as e:
        logger.warning("Failed to pre-fetch Ollama catalog on startup: %s", e)

    try:
        from backend.app.db import session as db_session

        if "pytest" not in sys.modules:
            db_session.get_engine()
            logger.info("System database initialized at %s", db_session.get_database_url())
    except Exception as e:
        logger.error("Failed to initialize system database on startup: %s", e)

    from backend.app.services.file_watcher import file_watcher
    await file_watcher.start()
    logger.info("File watcher started")

    # Clean up orphaned agent runs left behind by a previous crash/restart
    if "pytest" not in sys.modules:
        from backend.app.db.session import SessionLocal as _SessionLocal
        from backend.app.models.agent import AgentRun

        db = _SessionLocal()
        try:
            orphaned = db.query(AgentRun).filter(AgentRun.status == "running").count()
            if orphaned > 0:
                db.query(AgentRun).filter(AgentRun.status == "running").update(
                    {"status": "failed", "error": "Server restarted during execution"}
                )
                db.commit()
                logger.info("Cleaned up %d orphaned agent run(s)", orphaned)
        except Exception as e:
            logger.error("Failed to clean up orphaned agent runs: %s", e)
            db.rollback()
        finally:
            db.close()

    yield

    await file_watcher.stop()
    logger.info("File watcher stopped")

    try:
        await redis_cache.close()
    except Exception:
        pass  # event loop may already be closed during test teardown
    logger.info("Redis cache connection closed")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

app.add_middleware(RequestLoggingMiddleware)

setup_rate_limiting(app)
setup_csrf_protection(app)
setup_https_redirect(app)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(auth_router)
app.include_router(memory_router)
app.include_router(ws_router)
app.include_router(ws_system_router)


from fastapi import WebSocket, WebSocketDisconnect


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await manager.send(ws, {"echo": data})
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running 🚀"}
