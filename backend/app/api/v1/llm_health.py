"""LLM health and metrics endpoints."""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends

from backend.app.core.db import get_current_user
from backend.app.models.user import User
from backend.app.schemas.model import LLMHealthResponse, LLMMetricsResponse
from backend.app.services.intelligence.llm.manager import llm_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models/health", response_model=LLMHealthResponse)
async def llm_health(
    current_user: User = Depends(get_current_user),
):
    """Check health of all LLM providers."""
    start = time.monotonic()
    try:
        health = await llm_manager.health_check()
        latency_ms = (time.monotonic() - start) * 1000

        any_available = any(provider_info.get("available", False) for provider_info in health.values())
        status = "healthy" if any_available else "unavailable"
        error = None
        if not any_available:
            error = "No LLM providers available"

        return LLMHealthResponse(
            status=status,
            latency_ms=round(latency_ms, 1),
            error=error,
        )
    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        return LLMHealthResponse(
            status="error",
            latency_ms=round(latency_ms, 1),
            error=str(e),
        )


@router.get("/models/metrics", response_model=LLMMetricsResponse)
async def llm_metrics(
    current_user: User = Depends(get_current_user),
):
    """Return token usage and request metrics."""
    metrics = llm_manager.get_metrics()
    total_tokens = metrics.get("total_prompt_tokens", 0) + metrics.get("total_completion_tokens", 0)
    total_requests = metrics.get("total_requests", 0)

    return LLMMetricsResponse(
        total_requests=total_requests,
        total_tokens=total_tokens,
        avg_latency=0.0,
    )
