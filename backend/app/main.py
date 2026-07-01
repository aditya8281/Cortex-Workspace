"""
Entrypoint for the FastAPI app — Auth + Memory only.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path when running this file directly.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.api.memory import router as memory_router
from backend.app.api.router import api_router
from backend.app.api.ws import router as ws_router
from backend.app.auth.router import router as auth_router
from backend.app.core.config import settings
from backend.app.core.cors import CORSMiddlewareWithWS as CORSMiddleware
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
    UPLOAD_PATHS = {"/api/v1/me/profile/photo", "/api/v1/privacy/vault/files/upload"}

    async def dispatch(self, request: Request, call_next):
        # BaseHTTPMiddleware breaks WebSocket upgrades — bypass early
        if request.scope.get("type") == "websocket":
            return await call_next(request)
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                except (ValueError, TypeError):
                    return Response(status_code=400, content="Invalid Content-Length header")
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

    # Test Qdrant connectivity (optional — fails open, circuit breaker handles)
    from backend.app.core.vector_db import get_vector_db

    vdb = get_vector_db()
    if vdb.is_available:
        logger.info("Qdrant connected at %s:%s", settings.QDRANT_HOST, settings.QDRANT_PORT)
    else:
        logger.info(
            "Qdrant not available at %s:%s — vector search will degrade gracefully",
            settings.QDRANT_HOST,
            settings.QDRANT_PORT,
        )

    # Start event bus for cross-domain communication
    from backend.app.core.event_bus import event_bus
    from backend.app.core.event_handlers import on_download_completed  # noqa: F401

    await event_bus.start()
    logger.info("Event bus started")

    # Initialize LLM manager
    from backend.app.services.intelligence.llm.manager import llm_manager

    llm_manager.configure(
        llama_model_path=settings.LLM_MODEL_PATH or None,
        ollama_url=settings.OLLAMA_BASE_URL if settings.LLM_PROVIDER in ("auto", "ollama") else None,
        n_ctx=settings.LLM_CONTEXT_SIZE,
        n_gpu_layers=settings.LLM_GPU_LAYERS,
        n_threads=settings.LLM_THREADS,
        n_batch=settings.LLM_BATCH_SIZE,
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
        concurrency=settings.LLM_CONCURRENCY,
        use_mmap=settings.LLM_USE_MMAP,
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
            logger.info("System database initialized")
    except Exception as e:
        logger.error("Failed to initialize system database on startup: %s", e)

    from backend.app.services.awareness.file_watcher import get_file_watcher_v2

    get_file_watcher_v2().start()
    logger.info("File watcher started")

    # Start download manager for model downloads
    from backend.app.services.download.downloader import download_manager

    await download_manager.start()
    logger.info("Download manager started")

    if "pytest" not in sys.modules:
        try:
            from backend.app.db.session import SessionLocal as _SyncSession
            from backend.app.models.integration.sync_state import SyncState as _SyncState

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

    # Background library scrape (non-blocking — updates library.json once)
    if "pytest" not in sys.modules:
        try:
            from backend.app.services.intelligence.library_scraper import scrape_library_background

            asyncio.create_task(scrape_library_background())
            logger.info("Library scrape started in background")
        except Exception as e:
            logger.warning("Failed to start library scrape: %s", e)

    # Auto-detect Ollama models on startup
    if "pytest" not in sys.modules:
        try:
            from backend.app.db.session import SessionLocal as _SyncSessionLocal
            from backend.app.services.intelligence.ollama_sync import OllamaSyncService

            _sync_db = _SyncSessionLocal()
            try:
                _sync_result = await OllamaSyncService().sync_installed_models(_sync_db)
                logger.info(
                    "Ollama model sync: matched=%d created=%d deleted=%d",
                    _sync_result.matched,
                    _sync_result.created,
                    _sync_result.deleted,
                )
            finally:
                _sync_db.close()
        except Exception as e:
            logger.warning("Ollama model sync failed on startup: %s", e)

    # Clean up orphaned agent runs left behind by a previous crash/restart
    if "pytest" not in sys.modules:
        from backend.app.db.session import SessionLocal as _SessionLocal
        from backend.app.models.cognition.agent import AgentRun

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

    # Periodic Ollama model sync (every 60 seconds)
    if "pytest" not in sys.modules:

        async def _periodic_ollama_sync():
            while True:
                await asyncio.sleep(60)
                try:
                    from backend.app.db.session import SessionLocal as _PeriodicSession
                    from backend.app.services.intelligence.ollama_sync import OllamaSyncService

                    _pdb = _PeriodicSession()
                    try:
                        await OllamaSyncService().sync_installed_models(_pdb)
                    finally:
                        _pdb.close()
                except Exception as e:
                    logger.warning("Periodic Ollama sync failed: %s", e)

        asyncio.create_task(_periodic_ollama_sync())
        logger.info("Periodic Ollama model sync started (60s interval)")

    yield

    # Stop event bus
    try:
        from backend.app.core.event_bus import event_bus

        await event_bus.stop()
        logger.info("Event bus stopped")
    except Exception:
        logger.debug("Event bus stop skipped (test mode)")

    # Stop download manager
    try:
        from backend.app.services.download.downloader import download_manager

        await download_manager.stop()
        logger.info("Download manager stopped")
    except Exception:
        logger.debug("Download manager stop skipped (test mode)")

    try:
        from backend.app.services.awareness.file_watcher import get_file_watcher_v2

        get_file_watcher_v2().stop()
        logger.info("File watcher stopped")
    except Exception:
        logger.debug("File watcher stop skipped (test mode)")

    try:
        await redis_cache.close()
    except Exception:
        pass  # event loop may already be closed during test teardown
    logger.info("Redis cache connection closed")


def create_daemon_app() -> FastAPI:
    """Create a FastAPI app configured for daemon operation.

    Used by cortexd CLI. Returns the same app instance as the module-level
    ``app`` for backward compatibility.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        version=getattr(settings, "VERSION", "0.1.0"),
        lifespan=lifespan,
    )

    # ⚠️ Middleware stack: order matters. For EVERY BaseHTTPMiddleware subclass
    # that implements its own `dispatch`, you MUST add a WebSocket bypass:
    #     if request.scope.get("type") == "websocket":
    #         return await call_next(request)
    # Without this, ALL WebSocket connections silently break (uvicorn sends
    # a CORS-less 403 instead of the 101 upgrade).
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

    # NOTE: RateLimitMiddleware, CSRFMiddleware, and HTTPSRedirectMiddleware
    # are added inside setup_*() calls below — each HAS the WS bypass check.

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

    return app


# Module-level app for backward compatibility (existing imports / uvicorn)
app = create_daemon_app()


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running 🚀"}
