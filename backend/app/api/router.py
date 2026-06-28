"""Master API router — aggregates all domain routers.

After v1.02 domain reorganization, each domain router aggregates its sub-routers.
Endpoint files define their own paths (e.g., /knowledge/health, /users, /me/vault/files).
Domain routers include sub-routers WITHOUT prefixes — paths come from the endpoint files.
This master router includes domain routers WITHOUT extra prefixes — the
API_V1_PREFIX applied by main.py (/api/v1) is the only prefix needed.
"""

from fastapi import APIRouter

from backend.app.api.memory import router as memory_router
from backend.app.api.metrics import router as metrics_router
from backend.app.api.v1.awareness.router import router as awareness_router
from backend.app.api.v1.cognition.router import router as cognition_router
from backend.app.api.v1.developer.router import router as developer_router
from backend.app.api.v1.execution import router as execution_router
from backend.app.api.v1.integration.router import router as integration_router
from backend.app.api.v1.intelligence.router import router as intelligence_router
from backend.app.api.v1.interaction.router import router as interaction_router
from backend.app.api.v1.memory.router import router as v1_memory_router
from backend.app.api.v1.privacy.router import router as privacy_router
from backend.app.api.v1.system.router import router as system_router

api_router = APIRouter()

# ── Legacy domains (pre-v1.02, kept for backward compatibility) ──
api_router.include_router(memory_router, tags=["Memory"])
api_router.include_router(metrics_router, tags=["Metrics"])

# ── v1.02 domain routers (paths defined in endpoint files, no prefix here) ──
# IMPORTANT: Specific routes MUST be registered BEFORE parameterized routes.
# system_router (has /models/health, /models/metrics) and integration_router
# (has /models/installed) must come BEFORE developer_router (has /models/{model_id})
# and integration_router parameterized routes (has /models/{model_name}/download).
api_router.include_router(v1_memory_router, prefix="/memory", tags=["Knowledge", "Long-Term Memory", "Search"])
api_router.include_router(awareness_router, prefix="/awareness", tags=["Indexing", "Repository"])
api_router.include_router(cognition_router, tags=["Agents", "Cognition"])
api_router.include_router(execution_router, tags=["Execution"])
api_router.include_router(interaction_router, tags=["Conversations", "Notifications", "Profile", "Users", "WebSocket"])
api_router.include_router(system_router, tags=["Health", "System", "LLM Health", "WebSocket"])
api_router.include_router(intelligence_router, tags=["Models Intelligence"])
api_router.include_router(integration_router, tags=["Downloads", "Sync"])
api_router.include_router(privacy_router, prefix="/privacy", tags=["Settings", "Vault"])
api_router.include_router(developer_router, tags=["Models", "GitHub"])
