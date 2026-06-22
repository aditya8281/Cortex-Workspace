from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.conversation import Conversation
from backend.app.models.user import User

logger = logging.getLogger(__name__)
from backend.app.schemas.conversation import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationMessageResponse,
    ConversationResponse,
    CreateConversationRequest,
    SendMessageRequest,
)
from backend.app.services.conversation_service import (
    ConversationService,
    estimate_tokens,
)
from backend.app.services.rag_pipeline import get_rag_pipeline

router = APIRouter()


# ── CRUD Endpoints ──────────────────────────────────────────────────


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ConversationService(db)
    convs = svc.list(current_user.id, limit, offset)
    total = db.query(func.count(Conversation.id)).filter(Conversation.user_id == current_user.id).scalar()
    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(c) for c in convs],
        total=total,
    )


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    payload: CreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ConversationService(db)
    conv = svc.create(current_user.id, payload.title, payload.repo_id)
    return ConversationResponse.model_validate(conv)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
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
    return ConversationDetailResponse(
        id=conv.id,
        title=conv.title,
        repo_id=conv.repo_id,
        model_used=conv.model_used,
        message_count=conv.message_count,
        total_tokens=conv.total_tokens,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[ConversationMessageResponse.model_validate(m) for m in messages],
    )


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

    conv_before = svc.get(conversation_id, user_id) if user_id else None
    is_first_message = conv_before and (conv_before.message_count or 0) == 0

    # Save user message with token count
    user_tokens = estimate_tokens(user_content)
    svc.add_message(conversation_id, "user", user_content, tokens=user_tokens)

    # Update model_used on conversation
    if model and user_id:
        conv = svc.get(conversation_id, user_id)
        if conv:
            conv.model_used = model
            db.commit()

    # Build context using RAG pipeline (retrieves relevant knowledge + history)
    rag = get_rag_pipeline(db)
    conv = svc.get(conversation_id, user_id) if user_id else None
    repo_id = conv.repo_id if conv else None
    rag_context = rag.retrieve_context(user_content, repo_id=repo_id)
    sources = [{"file_path": r.file_path, "score": r.score, "content": r.content[:300]} for r in rag_context.results]

    history = svc.get_context_messages(conversation_id, max_tokens=28000)
    system_parts = ["You are Cortex, a helpful AI assistant with access to the user's codebase and knowledge."]
    if rag_context.formatted_context:
        system_parts.append(f"Relevant context from the codebase:\n\n{rag_context.formatted_context}")
        system_parts.append(
            "\nUse this context to answer the user's question. Cite sources using [1], [2], etc. when referencing specific files."
        )
    raw_messages = [{"role": "system", "content": "\n\n".join(system_parts)}]
    for msg in history:
        raw_messages.append({"role": msg.role, "content": msg.content})
    raw_messages.append({"role": "user", "content": user_content})
    messages = [LLMMessage(role=m["role"], content=m["content"]) for m in raw_messages]

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

    if is_first_message:
        title = await svc.generate_title(user_content, model=model)
        svc.update_title(conversation_id, title)

    # Send completion event
    yield f"data: {json.dumps({'type': 'done', 'total_tokens': response_tokens, 'sources': sources})}\n\n"


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ConversationService(db)
    conv = svc.get(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    async def _wrapped_stream():
        async for event in _stream_chat_response(
            conversation_id, payload.content, db, model=payload.model, user_id=current_user.id
        ):
            yield event
        background_svc = ConversationService(db)

        async def _extract_with_logging():
            try:
                await background_svc.extract_insights(conversation_id, current_user.id, model=payload.model)
            except Exception:
                logger.error("Background insight extraction failed for conversation %d", conversation_id, exc_info=True)

        task = asyncio.create_task(_extract_with_logging())
        task.add_done_callback(lambda t: None if not t.exception() else logger.error("Unhandled error in background task: %s", t.exception()))

    return StreamingResponse(
        _wrapped_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
