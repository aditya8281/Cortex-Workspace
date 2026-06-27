"""Privacy domain API router — Settings, Vault."""

from fastapi import APIRouter

from .settings import router as settings_router
from .vault import router as vault_router

router = APIRouter()
router.include_router(settings_router)
router.include_router(vault_router, prefix="/me/vault")
