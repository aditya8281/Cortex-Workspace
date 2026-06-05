from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.ai.exceptions import ModelNotInstalledError
from backend.app.ai.gateway import AIGateway

router = APIRouter()
gateway = AIGateway()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str | None = None
    model: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    query: str
    response: str
    execution_id: str | None = None
    routing_info: dict[str, Any] | None = None


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    try:
        result = await gateway.route(
            query=payload.message,
            llm_model=payload.model,
        )
        return ChatResponse(
            session_id=payload.session_id or f"chat-{uuid.uuid4().hex[:12]}",
            query=payload.message,
            response=result.answer,
            execution_id=result.execution_id,
            routing_info=result.routing_info,
        )
    except ModelNotInstalledError as exc:
        return ChatResponse(
            session_id=payload.session_id or f"chat-{uuid.uuid4().hex[:12]}",
            query=payload.message,
            response=f"Error: model {exc.model} is not installed.",
            execution_id=None,
            routing_info={"error": "model_not_installed", "model": exc.model},
        )
