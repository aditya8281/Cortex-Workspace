from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.conversation import Conversation
from backend.app.models.interaction.user import User
from backend.app.services.interaction.stream_manager import stream_manager

logger = logging.getLogger(__name__)
from backend.app.schemas.interaction.conversation import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationMessageResponse,
    ConversationResponse,
    CreateConversationRequest,
    SendMessageRequest,
)
from backend.app.services.intelligence.rag_pipeline import get_rag_pipeline
from backend.app.services.interaction.conversation import (
    ConversationService,
    estimate_tokens,
)

router = APIRouter()


def _get_svc(db: Session, user_id: int) -> ConversationService:
    """Get a ConversationService with filesystem workspace attached.

    Every endpoint that creates/reads/modifies conversations uses this.
    The workspace enables dual-write (DB + filesystem) automatically.
    """
    try:
        from backend.app.services.storage.factory import get_user_workspace

        ws = get_user_workspace(user_id, db)
        return ConversationService(db, workspace=ws)
    except Exception as exc:
        logger.debug("Workspace unavailable, DB-only mode: %s", exc)
        return ConversationService(db)


# Timeout for waiting on user tool approval (seconds)
_APPROVAL_TIMEOUT = 120.0


async def _wait_for_approval(conversation_id: int, call_id: str) -> bool:
    """Wait for user to approve or deny a tool call.

    Creates a future in the stream manager. The approval endpoint resolves it.
    Times out after _APPROVAL_TIMEOUT seconds (denies by default).
    """
    future = stream_manager.create_approval_future(conversation_id, call_id)
    try:
        return await asyncio.wait_for(future, timeout=_APPROVAL_TIMEOUT)
    except asyncio.TimeoutError:
        logger.info("Tool approval timed out for %s/%s", conversation_id, call_id)
        return False


# ── CRUD Endpoints ──────────────────────────────────────────────────


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = _get_svc(db, current_user.id)
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
    svc = _get_svc(db, current_user.id)
    conv = svc.create(current_user.id, payload.title, payload.repo_id)
    return ConversationResponse.model_validate(conv)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = _get_svc(db, current_user.id)
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
        messages=[ConversationMessageResponse.model_validate(m) for m in messages],  # type: ignore[attr-defined]
    )


class RenameConversationPayload(BaseModel):
    title: str


@router.patch("/conversations/{conversation_id}/title", response_model=dict)
async def rename_conversation(
    conversation_id: int,
    payload: RenameConversationPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = _get_svc(db, current_user.id)
    conv = svc.get(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    svc.update_title(conversation_id, payload.title.strip())
    return {"status": "updated", "title": payload.title.strip()}


@router.delete("/conversations/{conversation_id}", response_model=dict)
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = _get_svc(db, current_user.id)
    deleted = svc.delete(conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


# ── Background Generation Task ──────────────────────────────────────
# Runs independently of any HTTP connection. Chunks are pushed into
# a StreamBuffer that any number of SSE consumers can read from.


# Maximum tool-calling iterations for chat (prevents runaway loops)
_MAX_CHAT_TOOL_ITERATIONS = 8


async def _generate_response_task(
    conversation_id: int,
    user_content: str,
    user_id: int,
    model: str | None = None,
) -> None:
    """Background task: generate LLM response with tool-calling support.

    Runs a loop: LLM call → parse TOOL_CALL → execute tools → repeat.
    Final text response (no TOOL_CALL) is streamed to SSE consumers.
    DB write always happens — even if no consumer is connected.
    """
    try:
        await _generate_response_task_impl(conversation_id, user_content, user_id, model)
    except Exception as e:
        logger.critical(
            "UNHANDLED exception in _generate_response_task conv=%d: %s",
            conversation_id,
            e,
            exc_info=True,
        )
        buffer = stream_manager.get_buffer(conversation_id)
        if buffer and not buffer.done:
            error_msg = f"Generation error: {e}"
            buffer.push(
                f"data: {json.dumps({'type': 'chunk', 'content': error_msg, 'tokens': len(error_msg) // 4})}\n\n"
            )
            buffer.mark_done(error=str(e))


async def _generate_response_task_impl(
    conversation_id: int,
    user_content: str,
    user_id: int,
    model: str | None = None,
) -> None:
    """Implementation of _generate_response_task."""
    import re

    from backend.app.agents.loop import (
        _TOOL_CALL_START_RE,
        _extract_paren_block,
        _parse_tool_calls,
        _strip_tool_calls,
    )
    from backend.app.agents.tools.policy import default_policy
    from backend.app.agents.tools.registry import get_tool_registry
    from backend.app.db.session import SessionLocal
    from backend.app.services.intelligence.llm.manager import llm_manager
    from backend.app.services.intelligence.llm.provider import LLMMessage
    from backend.app.services.intelligence.tool_router import (
        build_tool_choice_hint,
        classify_intent_tools,
    )

    buffer = stream_manager.get_or_create_buffer(conversation_id)
    db = SessionLocal()

    svc = _get_svc(db, user_id)

    try:
        conv_before = svc.get(conversation_id, user_id)
        is_first_message = conv_before and (conv_before.message_count or 0) == 0
    except Exception:
        is_first_message = False

    # Save user message (dual-write: DB + filesystem)
    user_tokens = estimate_tokens(user_content)
    try:
        svc.add_message(conversation_id, "user", user_content, tokens=user_tokens)
        if model:
            conv = svc.get(conversation_id, user_id)
            if conv:
                conv.model_used = model
        db.commit()
    except Exception as exc:
        logger.error("Failed to save user message: %s", exc)
        db.rollback()

    # Build context via RAG (isolated session — never taint the main session)
    rag_context = None
    sources = []
    try:
        from backend.app.db.session import SessionLocal as RagSessionLocal

        rag_db = RagSessionLocal()
        try:
            rag = get_rag_pipeline(rag_db)
            conv = svc.get(conversation_id, user_id)
            repo_id = conv.repo_id if conv else None
            rag_result = rag.retrieve_context(user_content, repo_id=repo_id, user_id=user_id)
            sources = [
                {"file_path": r.file_path, "score": r.score, "content": r.content[:300]} for r in rag_result.results
            ]
            rag_context = rag_result
        finally:
            rag_db.close()
    except Exception:
        logger.error("RAG pipeline failed", exc_info=True)

    history = svc.get_context_messages(conversation_id, max_tokens=28000)

    # Build system prompt from personality config + memories (isolated session)
    from backend.app.services.personality.builder import build_system_prompt

    try:
        from backend.app.db.session import SessionLocal as MemorySessionLocal

        memory_db = MemorySessionLocal()
        try:
            system_content = build_system_prompt(
                memory_db, user_id=user_id, user_message=user_content, workspace=svc.workspace
            )
        finally:
            memory_db.close()
    except Exception as exc:
        logger.warning("Memory-backed system prompt failed, using fallback: %s", exc)
        system_content = build_system_prompt(None, user_id=None, user_message=user_content)

    # Add RAG context if available
    if rag_context and rag_context.formatted_context:
        context_block = rag_context.formatted_context
        system_content += f"\n\nRelevant context from the codebase:\n\n{context_block}"
        system_content += "\nCite sources using [1], [2], etc. when referencing specific files."

    # Add tool descriptions to system prompt
    registry = get_tool_registry()
    policy = default_policy()
    tool_lines: list[str] = []
    for t in registry.get_all():
        try:
            props = t.schema.get("function", {}).get("parameters", {}).get("properties", {})
            param_desc = (
                ", ".join(f"{name}: {prop.get('description', name)}" for name, prop in props.items()) if props else ""
            )
            req = " [REQUIRES APPROVAL]" if t.requires_approval else ""
            tool_lines.append(f"  - {t.name}: {t.description} ({param_desc}){req}")
        except Exception:
            tool_lines.append(f"  - {t.name}: {t.description}")

    if tool_lines:
        system_content += "\n\nAvailable tools:\n" + "\n".join(tool_lines)

        # Intent-based routing: classify the user message and inject tool hints.
        # This helps small models (3-8B) that might ignore the tool list.
        intent = classify_intent_tools(user_content)
        intent_hint = build_tool_choice_hint(intent)
        if intent_hint:
            system_content += intent_hint
            logger.info(
                "Intent router: %s (confidence=%.2f) — hint injected",
                intent.tools_needed or ["none"],
                intent.confidence,
            )

    # Build message history for LLM
    llm_messages = [LLMMessage(role="system", content=system_content)]
    for msg in history:  # type: ignore[attr-defined]
        llm_messages.append(LLMMessage(role=msg.role, content=msg.content))

    full_response = ""
    thinking_content = ""
    response_tokens = 0
    total_tool_calls = 0

    # No native tool detection — always use streaming + text-based TOOL_CALL
    # parsing for ALL iterations. This guarantees per-token delivery every time.

    try:
        for tool_iteration in range(_MAX_CHAT_TOOL_ITERATIONS):
            content = ""
            tool_calls = []
            streamed_visible = ""  # Text already pushed as chunk events

            # Streaming path — runs every iteration for per-token delivery.
            # State machine: _in_tool_call suppresses tool-call text from visible output.
            _in_tool_call = False
            _tool_buf = ""
            _rolling = ""  # Rolling window for TOOL_CALL detection across chunks
            _think_buf = ""  # Accumulator inside <think> tags
            _in_think = False

            async for chunk in llm_manager.chat_stream(
                llm_messages,
                model=model,
                max_tokens=2048,
                temperature=0.7,
            ):
                if chunk.get("type") == "thinking":
                    text = chunk.get("text", "")
                    if text:
                        thinking_content += text
                        buffer.push(f"data: {json.dumps({'type': 'thinking', 'content': text})}\n\n")
                    continue

                text = chunk.get("text", "")
                if not text:
                    continue

                # ── Handle <think> tags inline ──────────────────────
                if _in_think:
                    close_idx = text.find("</think>")
                    if close_idx != -1:
                        _think_buf += text[:close_idx]
                        if _think_buf:
                            thinking_content += _think_buf
                            buffer.push(f"data: {json.dumps({'type': 'thinking', 'content': _think_buf})}\n\n")
                        _think_buf = ""
                        _in_think = False
                        text = text[close_idx + 8 :]
                        if not text:
                            continue
                    else:
                        _think_buf += text
                        continue

                think_start = text.find("<think>")
                if think_start != -1:
                    before = text[:think_start]
                    if before:
                        content += before
                        streamed_visible += before
                        buffer.push(f"data: {json.dumps({'type': 'chunk', 'content': before})}\n\n")
                    after_start = text[think_start + 7 :]
                    close_idx = after_start.find("</think>")
                    if close_idx != -1:
                        think_text = after_start[:close_idx]
                        if think_text:
                            thinking_content += think_text
                            buffer.push(f"data: {json.dumps({'type': 'thinking', 'content': think_text})}\n\n")
                        text = after_start[close_idx + 8 :]
                        if not text:
                            continue
                    else:
                        _in_think = True
                        _think_buf = after_start
                        continue

                # ── Tool call detection with rolling buffer ─────────
                if _in_tool_call:
                    # Inside a TOOL_CALL — suppress from visible output
                    _tool_buf += text
                    open_idx = _tool_buf.find("(")
                    if open_idx != -1:
                        result = _extract_paren_block(_tool_buf, open_idx)
                        if result is not None:
                            # Tool call complete — add to content for post-parse
                            content += _tool_buf
                            _in_tool_call = False
                            _tool_buf = ""
                            _rolling = ""
                    continue

                # Normal mode: check for TOOL_CALL start via rolling window
                _rolling += text
                match = _TOOL_CALL_START_RE.search(_rolling)
                if match:
                    # Push text before tool call as visible
                    pre_tool = _rolling[:match.start()]
                    if pre_tool:
                        content += pre_tool
                        streamed_visible += pre_tool
                        buffer.push(f"data: {json.dumps({'type': 'chunk', 'content': pre_tool})}\n\n")

                    # Enter tool call mode
                    _tool_buf = _rolling[match.start():]
                    _in_tool_call = True
                    _rolling = ""

                    # Check if tool call completes in same buffer
                    open_idx = _tool_buf.find("(")
                    if open_idx != -1:
                        result = _extract_paren_block(_tool_buf, open_idx)
                        if result is not None:
                            content += _tool_buf
                            _in_tool_call = False
                            _tool_buf = ""
                    continue

                # No TOOL_CALL — this is visible content
                content += text
                streamed_visible += text
                buffer.push(f"data: {json.dumps({'type': 'chunk', 'content': text})}\n\n")

                # Keep rolling window bounded
                if len(_rolling) > 200:
                    _rolling = _rolling[-100:]

            # ── Post-stream: parse tool calls ────────────────────
            content = content.strip()
            tool_calls = _parse_tool_calls(content)

            # Post-stream <think> extraction (models that embed think tags)
            if not thinking_content and "<think>" in content:
                m = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
                if m:
                    thinking_content = m.group(1).strip()
                    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                    tool_calls = _parse_tool_calls(content)
                    if thinking_content:
                        buffer.push(f"data: {json.dumps({'type': 'thinking', 'content': thinking_content})}\n\n")

            logger.info(
                "Streaming complete iter=%d: %d chars, %d tool calls",
                tool_iteration,
                len(content),
                len(tool_calls),
            )

            if not tool_calls and not content:
                if tool_iteration == 0:
                    content = "I don't have a response for that right now."
                else:
                    break

            if tool_calls:
                # If text after tool calls wasn't streamed (suppressed), push it now
                full_visible = _strip_tool_calls(content)
                if full_visible:
                    if full_visible.startswith(streamed_visible):
                        new_text = full_visible[len(streamed_visible):]
                    else:
                        new_text = full_visible
                    if new_text:
                        buffer.push(f"data: {json.dumps({'type': 'chunk', 'content': new_text})}\n\n")

                for tc in tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc.get("args", {})

                    # Coerce arg types
                    tool_obj = registry.get(tool_name)
                    if tool_obj:
                        from backend.app.agents.loop import _coerce_args

                        tool_args = _coerce_args(tool_args, tool_obj.schema)

                    total_tool_calls += 1

                    # Emit tool_call event
                    buffer.push(f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name, 'args': tool_args})}\n\n")

                    # Check policy
                    decision = policy.evaluate(tool_name, tool_iteration)
                    if decision == "deny":
                        result_text = f"Tool '{tool_name}' was denied by security policy"
                        buffer.push(
                            f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': result_text, 'denied': True})}\n\n"
                        )
                        llm_messages.append(
                            LLMMessage(
                                role="user",
                                content=f"[Tool result for {tool_name}]: {result_text}",
                            )
                        )
                        continue

                    if decision == "ask":
                        # Approval required — wait for user decision
                        call_id = f"{conversation_id}_{total_tool_calls}"
                        buffer.push(
                            f"data: {json.dumps({'type': 'tool_approval', 'tool': tool_name, 'args': tool_args, 'call_id': call_id})}\n\n"
                        )

                        # Wait for approval/denial via the approval queue
                        approved = await _wait_for_approval(conversation_id, call_id)

                        if not approved:
                            result_text = f"Tool '{tool_name}' was denied by user"
                            buffer.push(
                                f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': result_text, 'denied': True})}\n\n"
                            )
                            llm_messages.append(
                                LLMMessage(
                                    role="user",
                                    content=f"[Tool result for {tool_name}]: {result_text}",
                                )
                            )
                            continue

                    # Execute the tool
                    try:
                        tool_result = await registry.execute(tool_name, **tool_args)
                    except Exception as exc:
                        tool_result = f"Tool '{tool_name}' execution error: {exc}"

                    # Truncate very long results
                    if len(tool_result) > 4000:
                        tool_result = tool_result[:4000] + "\n... (truncated)"

                    buffer.push(
                        f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': tool_result[:500]})}\n\n"
                    )
                    llm_messages.append(
                        LLMMessage(
                            role="user",
                            content=f"[Tool result for {tool_name}]: {tool_result}",
                        )
                    )

                # Continue loop — LLM will synthesize tool results
                continue

            # No tool calls — this is the final text response
            full_response = content
            # Strip leading/trailing quotes from model responses
            if len(full_response) >= 2 and full_response.startswith('"') and full_response.endswith('"'):
                full_response = full_response[1:-1]
            response_tokens = estimate_tokens(full_response)

            # Already streamed token-by-token — no final chunk push needed
            break

    except asyncio.CancelledError:
        logger.info("Generation cancelled for conversation %d", conversation_id)
        return
    except RuntimeError:
        fallback = "I need a local LLM to respond. Please download a model in Settings > Models."
        full_response = fallback
        response_tokens = estimate_tokens(fallback)
        buffer.push(f"data: {json.dumps({'type': 'chunk', 'content': fallback, 'tokens': response_tokens})}\n\n")
    except Exception as e:
        logger.error("Chat generation error for conversation %s: %s", conversation_id, e)
        error_msg = "An error occurred while generating a response. Please try again."
        full_response = error_msg
        response_tokens = estimate_tokens(error_msg)
        buffer.push(f"data: {json.dumps({'type': 'chunk', 'content': error_msg, 'tokens': response_tokens})}\n\n")

    # ALWAYS write assistant message to DB
    try:
        svc.add_message(
            conversation_id,
            "assistant",
            full_response,
            tokens=response_tokens,
            thinking_content=thinking_content or None,
        )
        db.commit()
    except Exception as exc:
        logger.error("Failed to write assistant response to DB: %s", exc)
        db.rollback()

    if is_first_message:
        try:
            title = await svc.generate_title(user_content, model=model)
            svc.update_title(conversation_id, title)
            db.commit()
        except Exception as exc:
            logger.error("Title generation failed: %s", exc)
            db.rollback()

    done_data = {
        "type": "done",
        "total_tokens": response_tokens,
        "sources": sources,
        "tool_calls": total_tool_calls,
    }
    buffer.mark_done(final_data=done_data)

    # Background insight extraction
    try:
        await svc.extract_insights(conversation_id, user_id, model=model)
    except Exception as exc:
        logger.error("Background insight extraction failed for conversation %d: %s", conversation_id, exc)

    try:
        db.close()
    except Exception:
        pass

    stream_manager.gc()


# ── Streaming Chat Endpoints ────────────────────────────────────────


@router.post("/conversations/{conversation_id}/messages", response_model=None)
async def send_message(
    conversation_id: int,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start generating a response. Returns immediately — generation runs in background.

    The frontend should subscribe to GET /conversations/{id}/stream after this.
    """
    logger.info(
        "send_message called: conv=%s user=%s content_len=%d",
        conversation_id,
        current_user.id,
        len(payload.content),
    )

    # Validate conversation exists and belongs to user
    svc = _get_svc(db, current_user.id)
    conv = svc.get(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if generation is already in progress for this conversation
    existing_buf = stream_manager.get_buffer(conversation_id)
    if existing_buf and not existing_buf.done:
        return {"status": "generating", "conversation_id": conversation_id}

    # Create buffer and start background task
    stream_manager.get_or_create_buffer(conversation_id)
    task = asyncio.create_task(
        _generate_response_task(
            conversation_id,
            payload.content,
            current_user.id,
            model=payload.model,
        )
    )
    stream_manager.register_task(conversation_id, task)

    return {"status": "generating", "conversation_id": conversation_id}


@router.get("/conversations/{conversation_id}/stream")
async def stream_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Subscribe to the streaming response for a conversation.

    Can be called before, during, or after generation:
    - Before generation: waits for chunks to appear
    - During generation: receives chunks in real-time
    - After generation: receives buffered chunks, then done event

    Multiple consumers can subscribe simultaneously (multi-tab support).
    """
    # Validate conversation belongs to user
    svc = _get_svc(db, current_user.id)
    conv = svc.get(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    buffer = stream_manager.get_buffer(conversation_id)
    if buffer is None:
        # Buffer may not exist yet if subscribed before POST completed
        buffer = await stream_manager.wait_for_buffer(conversation_id, timeout=10.0)

    if buffer is None:
        # No generation happening at all — return done immediately
        async def empty_stream():
            yield f"data: {json.dumps({'type': 'done', 'total_tokens': 0, 'sources': []})}\n\n"

        return StreamingResponse(
            empty_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    async def _sse_stream():
        """Read from the StreamBuffer and yield SSE events.

        On connect, yields ALL historical events (catch-up) so resubscribing
        consumers (e.g. after a tab switch) get the full response so far.
        Then continues reading live events from the queue.

        Includes safety timeout: if no data arrives for 5 consecutive reads
        (150s total), emit a done event so the frontend isn't stuck forever.
        """
        try:
            # Catch-up: yield everything this buffer has seen so far
            for event in buffer.get_catch_up():
                yield event
            # If generation already finished, yield done and return
            if buffer.done:
                if buffer.final_data:
                    yield f"data: {json.dumps(buffer.final_data)}\n\n"
                return
            # Live: read new events as they arrive
            empty_streak = 0
            while True:
                chunk = await buffer.read(timeout=30.0)
                if chunk is None:
                    # Generation complete and buffer drained
                    if buffer.final_data:
                        yield f"data: {json.dumps(buffer.final_data)}\n\n"
                    break
                if chunk:
                    empty_streak = 0
                    yield chunk
                else:
                    empty_streak += 1
                    if empty_streak >= 5:
                        logger.warning("SSE stream timeout for conversation %d", conversation_id)
                        if not buffer.done:
                            buffer.mark_done(error="Stream timeout")
                        if buffer.final_data:
                            yield f"data: {json.dumps(buffer.final_data)}\n\n"
                        break
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.error("SSE stream error for conversation %d: %s", conversation_id, exc)

    return StreamingResponse(
        _sse_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/conversations/{conversation_id}/cancel", response_model=dict)
async def cancel_generation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an in-progress generation."""
    svc = _get_svc(db, current_user.id)
    conv = svc.get(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    cancelled = stream_manager.cancel_generation(conversation_id)
    return {"status": "cancelled" if cancelled else "not_generating"}


class ToolApprovalPayload(BaseModel):
    call_id: str
    approved: bool


@router.post("/conversations/{conversation_id}/approve", response_model=dict)
async def approve_tool_call(
    conversation_id: int,
    payload: ToolApprovalPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve or deny a pending tool call.

    The generation task is awaiting this decision. Once resolved,
    the tool executes (or is skipped) and generation continues.
    """
    svc = _get_svc(db, current_user.id)
    conv = svc.get(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    resolved = stream_manager.resolve_approval(conversation_id, payload.call_id, payload.approved)
    if not resolved:
        return {"status": "not_found", "message": "No pending approval with that call_id"}

    return {"status": "resolved", "approved": payload.approved}
