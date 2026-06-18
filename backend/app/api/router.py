from fastapi import APIRouter

from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.profile import router as profile_router
from backend.app.api.v1.users import router as users_router

api_router = APIRouter()

api_router.include_router(
    health_router,
    tags=["Health"]
)

api_router.include_router(
    users_router,
    tags=["Users"]
)

api_router.include_router(
    profile_router,
    prefix="/me/profile",
    tags=["Profile"]
)
