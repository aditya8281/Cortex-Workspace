"""Cognition domain API router — agents, planning, errors, hypothesis, confidence."""

from fastapi import APIRouter

from .agents import router as agents_router
from .confidence import router as confidence_router
from .errors import router as errors_router
from .hypothesis import router as hypothesis_router
from .planning import router as planning_router

router = APIRouter()
router.include_router(agents_router)
router.include_router(planning_router, prefix="/planning", tags=["Cognition - Planning"])
router.include_router(errors_router, prefix="/errors", tags=["Cognition - Error Analysis"])
router.include_router(hypothesis_router, prefix="/hypothesis", tags=["Cognition - Hypothesis"])
router.include_router(confidence_router, prefix="/confidence", tags=["Cognition - Confidence"])
