from fastapi import APIRouter

# CRTX routes disabled — experimental future feature. See backend/app/api/v1/crtx.py.
# from backend.app.api.v1.crtx import router as crtx_router
from backend.app.api.v1.github import router as github_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.profile import router as profile_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.vault import router as vault_router
from backend.app.api.memory import router as memory_router

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

api_router.include_router(
    github_router,
    prefix="/me/github",
    tags=["GitHub"]
)

api_router.include_router(
    vault_router,
    prefix="/me/vault",
    tags=["Vault"]
)

api_router.include_router(
    memory_router,
    tags=["Memory"]
)

# CRTX routes disabled — experimental future feature (not part of current release).
# To re-enable, uncomment the import above and the include_router below.
# api_router.include_router(
#     crtx_router,
#     prefix="/me/crtx",
#     tags=["CRTX Export/Import"]
# )
