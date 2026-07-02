from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from backend.app.services.storage.user_workspace import UserWorkspace

logger = logging.getLogger(__name__)

import builtins

from backend.app.models.interaction.conversation import Conversation, ConversationMessage

# Approximate tokens per character (English text ~4 chars per token)
CHARS_PER_TOKEN = 4

# Context window: max tokens to keep in history
MAX_CONTEXT_TOKENS = 32000


def estimate_tokens(text: str) -> int:
    """Approximate token count from text length (uses tiktoken when available)."""
    from backend.app.agents.token_counter import count_tokens

    return count_tokens(text)


class ConversationService:
    """Dual-write conversation service — DB + filesystem simultaneously.

    When a workspace is provided, all writes go to both DB and filesystem.
    Filesystem is the long-term source of truth; DB is the query index.
    When no workspace is provided, DB-only mode (backward compat).
    """

    def __init__(self, db: Session, workspace: "UserWorkspace | None" = None):
        self._db = db
        self._ws = workspace

    def create(self, user_id: int, title: str = "New Conversation", repo_id: int | None = None) -> Conversation:
        conv = Conversation(user_id=user_id, title=title, repo_id=repo_id)
        self._db.add(conv)
        self._db.commit()
        self._db.refresh(conv)

        # Dual-write: register in filesystem index
        if self._ws:
            try:
                self._ws.conversations.index_entry(
                    conv.id, title=title, repo_id=repo_id,
                )
            except Exception as exc:
                logger.warning("Filesystem index write failed for conv %d: %s", conv.id, exc)

        return conv

    def list(self, user_id: int, limit: int = 50, offset: int = 0) -> list[Conversation]:
        return (
            self._db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get(self, conversation_id: int, user_id: int) -> Conversation | None:
        return (
            self._db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        tokens: int | None = None,
        thinking_content: str | None = None,
    ) -> ConversationMessage:
        if tokens is None:
            tokens = estimate_tokens(content)
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            thinking_content=thinking_content,
            tokens=tokens,
        )
        self._db.add(msg)
        conv = self._db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.message_count = (conv.message_count or 0) + 1
            conv.total_tokens = (conv.total_tokens or 0) + tokens
        self._db.commit()
        self._db.refresh(msg)

        # Dual-write: append to filesystem JSONL
        if self._ws:
            try:
                self._ws.conversations.append_message(
                    conversation_id, role, content, tokens=tokens,
                    thinking_content=thinking_content,
                )
            except Exception as exc:
                logger.warning("Filesystem message write failed for conv %d: %s", conversation_id, exc)

        return msg

    def get_messages(self, conversation_id: int, limit: int = 50) -> builtins.list[ConversationMessage]:
        return (
            self._db.query(ConversationMessage)
            .filter(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
            .limit(limit)
            .all()
        )

    def get_context_messages(
        self, conversation_id: int, max_tokens: int = MAX_CONTEXT_TOKENS
    ) -> builtins.list[ConversationMessage]:
        """Get messages that fit within the token budget, keeping most recent."""
        all_msgs: list[ConversationMessage] = self.get_messages(conversation_id, limit=500)
        if not all_msgs:
            return []

        total = 0
        kept: list[ConversationMessage] = []
        for msg in reversed(all_msgs):
            msg_tokens = msg.tokens or estimate_tokens(msg.content)
            if total + msg_tokens > max_tokens:
                break
            kept.append(msg)
            total += msg_tokens
        kept.reverse()
        return kept

    def delete(self, conversation_id: int, user_id: int) -> bool:
        conv = self.get(conversation_id, user_id)
        if conv:
            self._db.delete(conv)
            self._db.commit()
            # Dual-write: remove from filesystem
            if self._ws:
                try:
                    self._ws.conversations.delete_conversation(conversation_id)
                except Exception as exc:
                    logger.warning("Filesystem delete failed for conv %d: %s", conversation_id, exc)
            return True
        return False

    def update_title(self, conversation_id: int, title: str) -> None:
        conv = self._db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.title = title
            self._db.commit()
        # Dual-write: update filesystem index
        if self._ws:
            try:
                self._ws.conversations.update_index(conversation_id, title=title)
            except Exception as exc:
                logger.warning("Filesystem title update failed for conv %d: %s", conversation_id, exc)

    async def extract_insights(
        self, conversation_id: int, user_id: int, model: str | None = None
    ) -> builtins.list[dict]:
        """Extract long-term memories about the user from this conversation.

        Two extraction paths:
        1. LLM-based: rich, nuanced extraction via the configurable prompt.
        2. Heuristic fallback: simple pattern matching when LLM fails.

        At least ONE path should succeed. Cortex never forgets.
        """
        from backend.app.services.memory.long_term import LongTermMemoryService

        messages = self.get_messages(conversation_id, limit=50)
        if len(messages) < 2:
            return []

        ltm_svc = LongTermMemoryService(self._db)
        existing = ltm_svc.search(user_id, min_confidence=0.0, limit=200)

        # ── Path 1: LLM-based extraction (rich, nuanced) ─────────────────
        stored: builtins.list[dict] = []
        try:
            stored = await self._extract_via_llm(
                messages, existing, ltm_svc, user_id, conversation_id, model
            )
            if stored:
                logger.info(
                    "LLM extraction: %d memories for user %d (conv %d)",
                    len(stored), user_id, conversation_id,
                )
                return stored
        except Exception as e:
            logger.warning("LLM extraction failed for conv %d: %s", conversation_id, e)

        # ── Path 2: Heuristic fallback (always works, no LLM needed) ────
        try:
            stored = self._extract_via_heuristics(
                messages, existing, ltm_svc, user_id, conversation_id
            )
            if stored:
                logger.info(
                    "Heuristic extraction: %d memories for user %d (conv %d)",
                    len(stored), user_id, conversation_id,
                )
        except Exception as e:
            logger.warning("Heuristic extraction failed for conv %d: %s", conversation_id, e)

        return stored

    async def _extract_via_llm(
        self,
        messages: list,
        existing: list,
        ltm_svc: "LongTermMemoryService",
        user_id: int,
        conversation_id: int,
        model: str | None = None,
    ) -> builtins.list[dict]:
        """LLM-based memory extraction — the rich path."""
        import json
        import re

        from backend.app.core.config import settings
        from backend.app.services.intelligence.llm.manager import llm_manager
        from backend.app.services.intelligence.llm.provider import LLMMessage

        existing_summary = "\n".join(
            f"- [{m.category}] {m.title}: {m.content}" for m in existing
        ) if existing else "(no existing memories)"

        conversation_text = "\n".join(
            f"{m.role}: {m.content}" for m in messages  # type: ignore[attr-defined]
        )

        extraction_prompt = (
            settings.CORTEX_EXTRACTION_PROMPT
            .replace("{name}", settings.CORTEX_NAME)
            .replace("{existing_memories}", existing_summary)
            .replace("{conversation}", conversation_text)
        )

        llm_messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are a memory extraction system. Output ONLY a valid JSON array. "
                    "No markdown, no explanation, no code fences. Just the raw JSON array."
                ),
            ),
            LLMMessage(role="user", content=extraction_prompt),
        ]
        result = await llm_manager.chat(llm_messages, model=model, max_tokens=1500, temperature=0.3)

        raw = result.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        json_match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not json_match:
            return []
        insights = json.loads(json_match.group())

        # Build a set of significant words from user messages only
        # for cross-reference validation
        user_text = "\n".join(
            m.content for m in messages
            if getattr(m, "role", None) == "user"  # type: ignore[attr-defined]
        ).lower()
        # Extract meaningful words (4+ chars) from user text
        user_words = set(re.findall(r"\b[a-z]{4,}\b", user_text))

        stored = []
        for insight in insights:
            if not isinstance(insight, dict):
                continue
            category = insight.get("category", "fact")
            valid_cats = ("preference", "pattern", "correction", "fact", "context", "personality")
            if category not in valid_cats:
                category = "fact"
            title = str(insight.get("title", ""))[:50]
            content = str(insight.get("content", ""))[:200]
            if not title or not content:
                continue

            # Cross-reference validation: at least 2 significant words from
            # the extracted memory must appear in the actual user messages.
            # This prevents the LLM from storing fabricated memories.
            memory_words = set(re.findall(r"\b[a-z]{4,}\b", (title + " " + content).lower()))
            overlap = memory_words & user_words
            if len(overlap) < 2:
                logger.debug(
                    "Dropping ungrounded memory '%s' (only %d words match user text)",
                    title, len(overlap),
                )
                continue

            existing_match = next(
                (m for m in existing if m.title.lower() == title.lower()), None
            )
            if existing_match:
                existing_match.content = content
                existing_match.confidence = min(1.0, existing_match.confidence + 0.15)
                existing_match.access_count += 1
                existing_match.updated_at = func.now()
                stored.append({"id": existing_match.id, "category": category, "title": title, "updated": True})
            else:
                memory = ltm_svc.create(
                    user_id=user_id,
                    category=category,
                    title=title,
                    content=content,
                    source="conversation",
                    source_id=conversation_id,
                )
                stored.append({"id": memory.id, "category": category, "title": title})
        self._db.commit()
        return stored

    @staticmethod
    def _extract_via_heuristics(
        messages: list,
        existing: list,
        ltm_svc: "LongTermMemoryService",
        user_id: int,
        conversation_id: int,
    ) -> builtins.list[dict]:
        """Heuristic memory extraction — works without an LLM.

        Extracts facts about the user by scanning the conversation for:
        - Self-identification ("I'm a...", "my name is...", "I work as...")
        - Preferences ("I prefer...", "I like...", "I hate...")
        - Corrections ("actually...", "no, I meant...", "that's wrong")
        - Opinions ("X is better than Y", "I think...", "honestly...")
        - Emotional signals ("frustrated", "excited", "stuck on", "love this")

        Always stores conversation summary for context.
        """
        import re

        user_messages = [m for m in messages if getattr(m, "role", None) == "user"]  # type: ignore[attr-defined]
        if not user_messages:
            return []

        full_text = "\n".join(m.content for m in user_messages)  # type: ignore[attr-defined]

        # Don't re-extract if we already have a summary for this conversation
        already_has_summary = any(
            m.source == "conversation" and m.source_id == conversation_id
            for m in existing
        )

        stored: builtins.list[dict] = []
        existing_titles = {m.title.lower() for m in existing}

        def _store(category: str, title: str, content: str) -> None:
            title = title[:50]
            content = content[:200]
            if not title or not content or title.lower() in existing_titles:
                return
            existing_titles.add(title.lower())
            memory = ltm_svc.create(
                user_id=user_id,
                category=category,
                title=title,
                content=content,
                source="conversation",
                source_id=conversation_id,
            )
            stored.append({"id": memory.id, "category": category, "title": title})

        # ── Self-identification ──────────────────────────────────────
        id_patterns = [
            r"(?:I'm|I am|my name is|call me) ([^.!?\n]{2,40})",
            r"(?:I work (?:as|at|on)|I'm a) ([^.!?\n]{2,60})",
            r"(?:I (?:do|make|build|write|design|code)) ([^.!?\n]{2,60})",
        ]
        for pattern in id_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                _store("fact", f"self-identifies: {match.group(1)[:40]}", f"The user said: \"{match.group(0).strip()}\"")

        # ── Preferences ──────────────────────────────────────────────
        pref_patterns = [
            r"(?:I (?:prefer|like|love|enjoy|always use)) ([^.!?\n]{3,80})",
            r"(?:I (?:hate|despise|can't stand|dislike|never use)) ([^.!?\n]{3,80})",
            r"(?:I always|I never|I usually|I typically) ([^.!?\n]{3,80})",
        ]
        for pattern in pref_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                verb = match.group(0).split()[1] if len(match.group(0).split()) > 1 else "prefers"
                _store("preference", f"{verb}: {match.group(1)[:40]}", f"The user said: \"{match.group(0).strip()}\"")

        # ── Corrections ──────────────────────────────────────────────
        correction_patterns = [
            r"(?:actually|no[,.]?(?: I meant| that's wrong)|that's not right|wrong|incorrect)[,.]?\s*([^.!?\n]{5,120})",
            r"(?:I didn't (?:mean|say)|what I (?:meant|said|was trying)) [^.!?\n]{5,120}",
        ]
        for pattern in correction_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                _store("correction", f"corrected: {match.group(0)[:45]}", f"The user corrected: \"{match.group(0).strip()}\"")

        # ── Opinions / strong takes ──────────────────────────────────
        opinion_patterns = [
            r"(?:honestly|tbh|imo|in my opinion|I think) (?:that )?([^.!?\n]{5,120})",
            r"(?:X is|Y is) (?:better|worse|faster|slower|easier|harder) than ([^.!?\n]{5,80})",
        ]
        for pattern in opinion_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                _store("personality", f"opinion: {match.group(0)[:45]}", f"The user expressed: \"{match.group(0).strip()}\"")

        # ── Emotional signals ────────────────────────────────────────
        emotion_map = {
            "frustrated": "pattern", "excited": "personality",
            "stuck": "context", "love this": "personality",
            "hate this": "personality", "confused": "context",
            "annoyed": "personality", "impressed": "personality",
            "pissed off": "personality", "livid": "personality",
            "this is great": "personality", "this is garbage": "personality",
            "you're wrong": "correction", "that's wrong": "correction",
            "bullshit": "personality", "no way": "personality",
        }
        for keyword, category in emotion_map.items():
            if keyword in full_text.lower():
                for sentence in re.split(r"[.!?]", full_text):
                    if keyword in sentence.lower():
                        _store(category, f"felt {keyword}", f"The user expressed feeling {keyword}: \"{sentence.strip()}\"")
                        break

        # ── Conflict / fight detection ─────────────────────────────
        fight_patterns = [
            (r"(?:you(?:'re| are) (?:wrong|stupid|dumb|full of shit|bullshit|an idiot))", "fight with Cortex"),
            (r"(?:that(?:'s| is) (?:bullshit|stupid|wrong|garbage|trash|nonsense))", "disagreement"),
            (r"(?:I (?:disagree|don't agree|call bullshit))", "disagreement"),
            (r"(?:you (?:don't understand|aren't listening|don't get it))", "frustrated with Cortex"),
            (r"(?:this (?:sucks|is terrible|is awful|is garbage|is broken))", "frustrated with tool"),
            (r"(?:I (?:give up|can't deal|am done))", "gave up on something"),
            (r"(?:sorry|my bad|I was wrong|I apologize)", "apologized"),
            (r"(?:never mind|forget it|whatever|fine)", "dismissed"),
        ]
        for pattern, label in fight_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                # Find the sentence for context
                context_sentence = ""
                for sentence in re.split(r"[.!?]", full_text):
                    if match.group(0).lower() in sentence.lower():
                        context_sentence = sentence.strip()[:150]
                        break
                _store(
                    "correction",
                    f"{label}: {match.group(0)[:40]}",
                    f"The user said: \"{context_sentence or match.group(0)}\"",
                )

        # ── Conversation emotional arc ─────────────────────────────
        # Detect the overall emotional trajectory of the conversation
        all_text_lower = full_text.lower()
        positive_words = sum(1 for w in ["great", "awesome", "love", "nice", "perfect", "thanks", "exactly", "yes"] if w in all_text_lower)
        negative_words = sum(1 for w in ["hate", "wrong", "stupid", "broken", "bug", "frustrat", "annoy", "suck", "shit", "damn"] if w in all_text_lower)
        total = positive_words + negative_words
        if total >= 2:
            if negative_words > positive_words * 1.5:
                _store("context", f"tense conversation (neg:{negative_words} pos:{positive_words})",
                       f"Conversation had {negative_words} negative signals vs {positive_words} positive. User was likely frustrated.")
            elif positive_words > negative_words * 1.5:
                _store("personality", f"positive conversation (pos:{positive_words} neg:{negative_words})",
                       f"Conversation had {positive_words} positive signals vs {negative_words} negative. User was likely in a good mood.")

        # ── Conversation summary (always stored) ─────────────────────
        if not already_has_summary and len(user_messages) >= 2:
            summary_text = " ".join(m.content[:200] for m in user_messages[:5])  # type: ignore[attr-defined]
            _store(
                "context",
                f"conversation about: {summary_text[:45]}",
                f"Conversation had {len(user_messages)} user messages. Topics: {summary_text[:195]}",
            )

        if stored:
            ltm_svc.db.commit()

        return stored

    async def generate_title(self, content: str, model: str | None = None) -> str:
        try:
            from backend.app.services.intelligence.llm.manager import llm_manager
            from backend.app.services.intelligence.llm.provider import LLMMessage

            messages = [
                LLMMessage(
                    role="system",
                    content="Generate a short conversation title (3-5 words) from the user's message. Reply with ONLY the title, no quotes or punctuation.",
                ),
                LLMMessage(role="user", content=content),
            ]
            result = await llm_manager.chat(messages, model=model, max_tokens=20, temperature=0.3)
            title = result.content.strip().strip('"').strip("'")
            if 3 <= len(title) <= 80:
                return title
        except Exception:
            logger.debug("LLM title generation failed, using fallback", exc_info=True)
        return content[:50].strip()
