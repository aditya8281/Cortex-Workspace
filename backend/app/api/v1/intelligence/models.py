"""Models API — main router that includes sub-routers."""

from fastapi import APIRouter

from backend.app.api.v1.catalog import router as catalog_router
from backend.app.api.v1.downloads import router as downloads_router
from backend.app.api.v1.llm_health import router as llm_health_router
from backend.app.api.v1.settings import router as settings_router

router = APIRouter()

# Order matters: include routers with only specific routes first,
# then catalog_router last (it has /models/{model_id} which would
# swallow /models/health, /models/installed, etc. if registered first).
router.include_router(llm_health_router)
router.include_router(settings_router)
router.include_router(downloads_router)
router.include_router(catalog_router)
