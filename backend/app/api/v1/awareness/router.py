"""Awareness domain API router — Indexing, Repository."""

from fastapi import APIRouter

from .indexing import router as indexing_router
from .repository import router as repository_router

router = APIRouter()
router.include_router(indexing_router)
router.include_router(repository_router)
