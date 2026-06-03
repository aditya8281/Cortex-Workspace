from contextlib import asynccontextmanager
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.core.middleware import RequestLoggingMiddleware
from backend.app.models.user import User  # noqa: F401
from backend.app.models.user_profile import UserProfile  # noqa: F401
from backend.app.ai.memory.models import Memory  # noqa: F401
from backend.app.intelligence.models import (  # noqa: F401
    CortexAutomationSettings,
    KnowledgeEntry,
    PendingSystemAction,
    ProactiveNotification,
    RepositoryProfile,
    SyncRun,
)
from backend.app.core.logging import get_logger


setup_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} started")
    
    # Background warmup for AIExecutor and RAG index loading to optimize first-query latency
    import asyncio
    from backend.app.executor import AIExecutor

    def warmup_executor():
        try:
            logger.info("Starting background warmup: Loading models and initializing RAG index...")
            executor = AIExecutor()
            executor.rag.initialize()
            logger.info("Background warmup complete: AIExecutor and RAGService are fully ready.")
        except Exception as ex:
            logger.error(f"Error during background warmup: {ex}")

    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, warmup_executor)

    from backend.app.intelligence.observer_service import BackgroundObserverService

    observer = BackgroundObserverService(poll_interval_seconds=90)
    observer.start(loop=loop)
    logger.info("Cortex background observer started")

    yield

    observer.stop()


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

@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} is running 🚀"
    }