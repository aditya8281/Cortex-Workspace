from fastapi import APIRouter

from backend.app.api.metrics import router as metrics_router
from backend.app.api.v1.github import router as github_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.notifications import router as notifications_router
from backend.app.api.v1.profile import router as profile_router
from backend.app.api.v1.repository import router as repository_router
from backend.app.api.v1.search import router as search_router
from backend.app.api.v1.system import router as system_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.vault import router as vault_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])

api_router.include_router(users_router, tags=["Users"])

api_router.include_router(profile_router, prefix="/me/profile", tags=["Profile"])

api_router.include_router(github_router, prefix="/me/github", tags=["GitHub"])

api_router.include_router(vault_router, prefix="/me/vault", tags=["Vault"])

api_router.include_router(metrics_router, tags=["Metrics"])

api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])

api_router.include_router(system_router, tags=["System"])

api_router.include_router(search_router, tags=["Search"])

api_router.include_router(repository_router, tags=["Repository"])
