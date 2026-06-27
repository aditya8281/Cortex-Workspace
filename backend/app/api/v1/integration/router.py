"""Integration domain API router — Downloads, Sync."""

from fastapi import APIRouter

from .downloads import router as downloads_router
from .sync import router as sync_router

router = APIRouter()
router.include_router(downloads_router)
router.include_router(sync_router)
