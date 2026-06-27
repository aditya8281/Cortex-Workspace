"""Privacy & Trust API — RBAC, ABAC, audit, consent, export, transparency."""

from fastapi import APIRouter

from .access_control import router as access_control_router
from .audit import router as audit_router
from .consent import router as consent_router
from .export import router as export_router
from .transparency import router as transparency_router

router = APIRouter()
router.include_router(audit_router, prefix="/audit", tags=["Privacy - Audit Logging"])
router.include_router(consent_router, prefix="/consent", tags=["Privacy - Consent"])
router.include_router(export_router, prefix="/export", tags=["Privacy - Data Export"])
router.include_router(transparency_router, prefix="/transparency", tags=["Privacy - Transparency"])
router.include_router(access_control_router, prefix="/access", tags=["Privacy - Access Control"])
