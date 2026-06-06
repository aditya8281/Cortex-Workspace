from fastapi import APIRouter

from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.ai import router as ai_router
from backend.app.api.v1.execution import router as execution_router
from backend.app.api.v1.models import router as models_router
from backend.app.api.v1.user_settings import router as user_settings_router
from backend.app.api.v1.workspace import router as workspace_router
from backend.app.api.v1.sync import router as sync_router
from backend.app.api.v1.intelligence import router as intelligence_router
from backend.app.api.v1.profile import router as profile_router
from backend.app.api.v1.context import router as context_router
from backend.app.api.v1.hierarchical import router as hierarchical_router
from backend.app.api.v1.orchestration import router as orchestration_router
from backend.app.api.v1.vault import router as vault_router
from backend.app.api.v1.brain_vault import router as brain_vault_router
from backend.app.api.v1.registry import router as registry_router

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
    ai_router,
    prefix="/ai",
    tags=["AI"]
)

api_router.include_router(
    execution_router,
    prefix="/execution",
    tags=["Execution"]
)

api_router.include_router(
    models_router,
    prefix="/models",
    tags=["Models"]
)

api_router.include_router(
    user_settings_router,
    prefix="/users/me/settings",
    tags=["User Settings"]
)

api_router.include_router(
    workspace_router,
    prefix="/workspace",
    tags=["Workspace"]
)

api_router.include_router(
    sync_router,
    prefix="/sync",
    tags=["Sync"]
)

api_router.include_router(
    hierarchical_router,
    prefix="/sync/hierarchical",
    tags=["Hierarchical Memory"]
)

api_router.include_router(
    intelligence_router,
    prefix="/intelligence",
    tags=["Intelligence"]
)

api_router.include_router(
    profile_router,
    prefix="/me/profile",
    tags=["Profile"]
)

api_router.include_router(
    context_router,
    prefix="/context",
    tags=["Context"]
)

api_router.include_router(
    orchestration_router,
    prefix="/sync/orchestration",
    tags=["Multi-Agent Orchestration"]
)

api_router.include_router(
    vault_router,
    prefix="/vault",
    tags=["Vault"]
)

api_router.include_router(
    brain_vault_router,
    prefix="/brain/vault",
    tags=["Brain Vault"]
)

api_router.include_router(
    registry_router,
    tags=["Ollama Registry"]
)
