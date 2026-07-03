"""Personality builder — constructs the system prompt from config + memories.

This is the single source of truth for what Cortex says about itself
and what it knows about the user. Every string is configurable via
.config.py settings (CORTEX_*). Power users own their own personality.

Usage::

    from backend.app.services.personality.builder import build_system_prompt

    prompt = build_system_prompt(user_id=1, user_message="hello", db=session)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.app.core.config import settings

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from backend.app.services.memory.long_term import LongTermMemoryService
    from backend.app.services.storage.user_workspace import UserWorkspace

logger = logging.getLogger(__name__)

# Maximum tokens for the memory block (keeps system prompt from eating context)
_MAX_MEMORY_TOKENS = 2000  # ~500 words, enough for rich memory without bloat
# Rough heuristic: 1 token ≈ 4 chars
_MAX_MEMORY_CHARS = _MAX_MEMORY_TOKENS * 4


def _format_memories(memories: list) -> str:
    """Format memories into a natural, human-readable block.

    Memories are grouped by category and written in first-person voice
    so the system prompt reads like Cortex's actual internal monologue,
    not a database dump.
    """
    if not memories:
        return ""

    # Group by category
    grouped: dict[str, list] = {}
    for m in memories:
        cat = getattr(m, "category", "fact") or "fact"
        grouped.setdefault(cat, []).append(m)

    # Category labels — structured, clinical, to prevent LLM from treating as narrative
    cat_headers = {
        "personality": "PERSONALITY",
        "preference": "PREFERENCES",
        "pattern": "PATTERNS",
        "correction": "CORRECTIONS",
        "fact": "KNOWN FACTS",
        "context": "CONTEXT",
    }

    lines: list[str] = []
    for cat in ("personality", "preference", "pattern", "correction", "fact", "context"):
        items = grouped.get(cat, [])
        if not items:
            continue
        label = cat_headers.get(cat, cat.upper())
        lines.append(f"  {label}")
        for m in items:
            title = getattr(m, "title", "")
            content = getattr(m, "content", "")
            if title and content:
                lines.append(f"    · {title} — {content}")
            elif content:
                lines.append(f"    · {content}")
        lines.append("")

    result = "\n".join(lines).strip()

    # Truncate if too long
    if len(result) > _MAX_MEMORY_CHARS:
        result = result[:_MAX_MEMORY_CHARS] + "\n  ... (more memories truncated)"

    return result


def _retrieve_memories(
    ltm: LongTermMemoryService,
    user_id: int,
    user_message: str | None = None,
) -> list:
    """Retrieve memories using a multi-signal approach.

    Strategy:
      1. ALWAYS get the top-N highest-confidence memories (the "core identity" memories).
      2. ALSO search for message-relevant memories via ILIKE.
      3. Merge, dedup by id, and return the union.

    This ensures Cortex ALWAYS knows the user's basics (name, personality,
    preferences, corrections) even when the current message is unrelated
    to any stored memory. The ILIKE search adds topical relevance on top.
    """
    # 1. Core identity: always the highest-confidence memories
    #    These are the things Cortex knows about the user NO MATTER WHAT.
    #    min_confidence=0.3 filters out low-quality or fabricated memories.
    core = ltm.search(user_id, min_confidence=0.3, limit=7)

    # 2. Topical: relevance-based search
    relevant = []
    if user_message:
        relevant = ltm.search(user_id, query=user_message, min_confidence=0.3, limit=3)

    # 3. Merge by id, core first (higher confidence), then topical
    seen_ids: set[int] = set()
    merged: list = []
    for m in core:
        if m.id not in seen_ids:
            seen_ids.add(m.id)
            merged.append(m)
    for m in relevant:
        if m.id not in seen_ids:
            seen_ids.add(m.id)
            merged.append(m)

    return merged


def build_system_prompt(
    db: Session | None,
    user_id: int | None = None,
    user_message: str | None = None,
    workspace: UserWorkspace | None = None,
) -> str:
    """Build the complete system prompt for Cortex.

    Assembles the personality template from config, injects long-term
    memories if available, and returns the full system prompt string.

    Args:
        db: Database session
        user_id: Current user ID (for memory retrieval). If None, no memories.
        user_message: The user's current message (for relevance-based memory search).
        workspace: Optional UserWorkspace for filesystem-backed memory dual-read.

    Returns:
        Complete system prompt string ready for the LLM.
    """
    name = settings.CORTEX_NAME
    system_prompt = settings.CORTEX_SYSTEM_PROMPT.format(name=name)

    # Inject user profile data (what the user says about themselves)
    if user_id is not None and db is not None:
        try:
            from backend.app.models.interaction.user import User as UserModel

            user = db.get(UserModel, user_id)
            if user:
                profile_lines = []
                if user.full_name:
                    profile_lines.append(f"  Name: {user.full_name}")
                if user.nickname:
                    profile_lines.append(f"  Nickname: {user.nickname}")
                if user.bio:
                    profile_lines.append(f"  Bio: {user.bio}")
                if user.description:
                    profile_lines.append(f"  Description: {user.description}")
                if user.programming_languages:
                    langs = ", ".join(user.programming_languages)
                    profile_lines.append(f"  Languages: {langs}")
                if user.frameworks:
                    fw = ", ".join(user.frameworks)
                    profile_lines.append(f"  Frameworks: {fw}")
                if user.current_projects:
                    projects = "; ".join(user.current_projects)
                    profile_lines.append(f"  Projects: {projects}")
                if user.contribution_style:
                    profile_lines.append(f"  Contribution style: {user.contribution_style}")
                if user.handles:
                    handles = ", ".join(f"{k}: {v}" for k, v in user.handles.items())
                    profile_lines.append(f"  Social: {handles}")

                if profile_lines:
                    profile_block = "\n".join(profile_lines)
                    system_prompt += settings.CORTEX_PROFILE_TEMPLATE.format(profile=profile_block)
                    logger.info("Injected profile for user %d", user_id)
        except Exception as exc:
            logger.warning("Profile injection failed for user %d: %s", user_id, exc)

    # Inject memories
    if user_id is not None and db is not None:
        try:
            from backend.app.services.memory.long_term import LongTermMemoryService

            ltm = LongTermMemoryService(db, workspace=workspace)
            memories = _retrieve_memories(ltm, user_id, user_message)

            if memories:
                formatted = _format_memories(memories)
                if formatted:
                    memory_block = settings.CORTEX_MEMORY_TEMPLATE.format(name=name, memories=formatted)
                    system_prompt += memory_block
                    logger.info(
                        "Injected %d memories for user %d (total %d chars)",
                        len(memories),
                        user_id,
                        len(system_prompt),
                    )

                    # Reinforce memories that were accessed (gentle — prevents runaway)
                    for m in memories:
                        try:
                            ltm.reinforce(m.id, amount=0.01)
                        except Exception:
                            pass  # Don't let reinforcement failures break chat
            else:
                logger.info("No memories found for user %d", user_id)
        except Exception as exc:
            logger.warning("Memory retrieval failed for user %d: %s", user_id, exc)

    return system_prompt
