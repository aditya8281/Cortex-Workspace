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
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.api.auth import router as auth_router
from backend.app.api.memory import router as memory_router
from backend.app.api.router import api_router
from backend.app.api.v1.ws_models import router as ws_models_router
from backend.app.api.v1.ws_system import router as ws_system_router
from backend.app.api.ws import router as ws_router
from backend.app.core.config import settings
from backend.app.core.csrf import setup_csrf_protection
from backend.app.core.https_redirect import setup_https_redirect
from backend.app.core.logging import get_logger, setup_logging
from backend.app.core.middleware import RequestLoggingMiddleware
from backend.app.core.rate_limit import setup_rate_limiting
from backend.app.core.system_paths import ensure_system_dirs
from backend.app.db.bootstrap import bootstrap_database

setup_logging()

logger = get_logger(__name__)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent OOM attacks."""

    # 10MB default, 2MB for upload endpoints
    DEFAULT_LIMIT = 10 * 1024 * 1024  # 10MB
    UPLOAD_PATHS = {"/api/v1/me/profile/photo", "/api/v1/me/vault/files"}

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length:
                size = int(content_length)
                limit = 2 * 1024 * 1024 if request.url.path in self.UPLOAD_PATHS else self.DEFAULT_LIMIT
                if size > limit:
                    return Response(status_code=413, content="Request too large")
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} started")

    ensure_system_dirs()

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

    from backend.app.services.file_watcher_v2 import get_file_watcher_v2

    get_file_watcher_v2().start()
    logger.info("File watcher started")

    # Start download manager for model downloads
    from backend.app.services.model_downloader import download_manager

    await download_manager.start()
    logger.info("Download manager started")

    if "pytest" not in sys.modules:
        try:
            from backend.app.db.session import SessionLocal as _SyncSession
            from backend.app.models.sync_state import SyncState as _SyncState

            _sdb = _SyncSession()
            try:
                active_states = _sdb.query(_SyncState).filter(_SyncState.status == "active").all()
                _watcher = get_file_watcher_v2()
                for state in active_states:
                    _watcher.watch(state.repo_path)
                if active_states:
                    logger.info("Recovered %d active sync state(s)", len(active_states))
            finally:
                _sdb.close()
        except Exception as e:
            logger.warning("Failed to recover sync states on startup: %s", e)

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

    # Stop download manager
    try:
        from backend.app.services.model_downloader import download_manager

        await download_manager.stop()
        logger.info("Download manager stopped")
    except Exception:
        logger.debug("Download manager stop skipped (test mode)")

    try:
        from backend.app.services.file_watcher_v2 import get_file_watcher_v2

        get_file_watcher_v2().stop()
        logger.info("File watcher stopped")
    except Exception:
        logger.debug("File watcher stop skipped (test mode)")

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

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(RequestSizeLimitMiddleware)

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
app.include_router(ws_models_router)
app.include_router(ws_system_router)


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running 🚀"}
