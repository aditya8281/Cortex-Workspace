from fastapi import FastAPI

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.core.middleware import RequestLoggingMiddleware
from backend.app.models.user import User  # noqa: F401
from backend.app.ai.memory.models import Memory  # noqa: F401
from backend.app.core.logging import get_logger


setup_logging()

logger = get_logger(__name__)



app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
)

app.add_middleware(
    RequestLoggingMiddleware
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)

@app.on_event("startup")
async def startup_event():

    logger.info(
        f"{settings.APP_NAME} started"
    )
    
@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} is running 🚀"
    }