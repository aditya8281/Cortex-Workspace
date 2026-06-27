"""Developer domain API router — Catalog, GitHub."""

from fastapi import APIRouter

from .catalog import router as catalog_router
from .github import router as github_router

router = APIRouter()
router.include_router(catalog_router)
router.include_router(github_router, prefix="/me/github")
