"""Awareness domain API router — Indexing, Repository, Files, Device, Health, Environment, Project."""

from fastapi import APIRouter

from .device import router as device_router
from .environment import router as environment_router
from .files import router as files_router
from .health import router as health_router
from .indexing import router as indexing_router
from .project import router as project_router
from .repository import router as repository_router

router = APIRouter()
router.include_router(indexing_router)
router.include_router(repository_router)
router.include_router(files_router)
router.include_router(device_router)
router.include_router(health_router)
router.include_router(environment_router)
router.include_router(project_router)
