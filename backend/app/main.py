from fastapi import FastAPI

from backend.app.core.config import settings
from backend.app.api.router import api_router
from backend.app.models.user import User  # noqa: F401 - Registers User model


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0"
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX
)


@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} is running 🚀"
    }