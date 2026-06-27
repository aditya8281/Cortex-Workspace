"""System domain API router — Health, System, LLM Health, WS System."""

from fastapi import APIRouter

from .health import router as health_router
from .llm_health import router as llm_health_router
from .system import router as system_router
from .ws_system import router as ws_system_router

router = APIRouter()
router.include_router(health_router)
router.include_router(system_router)
router.include_router(llm_health_router)
router.include_router(ws_system_router)
