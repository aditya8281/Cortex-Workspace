from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.conversation_service import (
    ConversationService,
    estimate_tokens,
)

router = APIRouter()


class CreateConversationPayload(BaseModel):
    title: str = "New Conversation"
    repo_id: int | None = None


class SendMessagePayload(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    model: str | None = None


# ── CRUD Endpoints ──────────────────────────────────────────────────


@router.get("/conversations")
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ConversationService(db)
    convs = svc.list(current_user.id, limit, offset)
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "repo_id": c.repo_id,
                "model_used": c.model_used,
                "message_count": c.message_count,
                "total_tokens": c.total_tokens,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in convs
        ]
    }


@router.post("/conversations")
async def create_conversation(
    payload: CreateConversationPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ConversationService(db)
    conv = svc.create(current_user.id, payload.title, payload.repo_id)
    return {"id": conv.id, "title": conv.title}


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ConversationService(db)
    conv = svc.get(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = svc.get_messages(conversation_id)
    return {
        "id": conv.id,
        "title": conv.title,
        "model_used": conv.model_used,
        "total_tokens": conv.total_tokens,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "tokens": m.tokens,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ConversationService(db)
    deleted = svc.delete(conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


# ── Streaming Chat Endpoint ─────────────────────────────────────────


async def _stream_chat_response(
    conversation_id: int,
    user_content: str,
    db: Session,
    model: str | None = None,
    user_id: int | None = None,
) -> AsyncGenerator[str, None]:
    """Generator that yields SSE events for the chat response."""
    from backend.app.services.llm.manager import llm_manager
    from backend.app.services.llm.provider import LLMMessage

    svc = ConversationService(db)

    # Save user message with token count
    user_tokens = estimate_tokens(user_content)
    svc.add_message(conversation_id, "user", user_content, tokens=user_tokens)

    # Update model_used on conversation
    if model and user_id:
        conv = svc.get(conversation_id, user_id)
        if conv:
            conv.model_used = model
            db.commit()

    # Build context from conversation history (token-budget aware)
    history = svc.get_context_messages(conversation_id)
    messages = [LLMMessage(role=m.role, content=m.content) for m in history]

    full_response = ""
    response_tokens = 0

    try:
        async for chunk in llm_manager.chat_stream(messages, model=model, max_tokens=2048, temperature=0.7):
            full_response += chunk
            response_tokens = estimate_tokens(full_response)
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'tokens': response_tokens})}\n\n"
    except RuntimeError:
        # LLM not available — return a fallback message
        fallback = "I need a local LLM to respond. Please download a model in Settings > Models."
        full_response = fallback
        response_tokens = estimate_tokens(fallback)
        yield f"data: {json.dumps({'type': 'chunk', 'content': fallback, 'tokens': response_tokens})}\n\n"
    except Exception as e:
        error_msg = f"Error: {str(e)[:200]}"
        full_response = error_msg
        response_tokens = estimate_tokens(error_msg)
        yield f"data: {json.dumps({'type': 'chunk', 'content': error_msg, 'tokens': response_tokens})}\n\n"

    # Save assistant message with token count
    svc.add_message(conversation_id, "assistant", full_response, tokens=response_tokens)

    # Send completion event
    yield f"data: {json.dumps({'type': 'done', 'total_tokens': response_tokens})}\n\n"


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    payload: SendMessagePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ConversationService(db)
    conv = svc.get(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return StreamingResponse(
        _stream_chat_response(conversation_id, payload.content, db, model=payload.model, user_id=current_user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
