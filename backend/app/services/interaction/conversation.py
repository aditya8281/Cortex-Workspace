from __future__ import annotations

import logging

from sqlalchemy.orm import Session

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
    def __init__(self, db: Session):
        self._db = db

    def create(self, user_id: int, title: str = "New Conversation", repo_id: int | None = None) -> Conversation:
        conv = Conversation(user_id=user_id, title=title, repo_id=repo_id)
        self._db.add(conv)
        self._db.commit()
        self._db.refresh(conv)
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
    ) -> ConversationMessage:
        if tokens is None:
            tokens = estimate_tokens(content)
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens=tokens,
        )
        self._db.add(msg)
        conv = self._db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.message_count = (conv.message_count or 0) + 1
            conv.total_tokens = (conv.total_tokens or 0) + tokens
        self._db.commit()
        self._db.refresh(msg)
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
            return True
        return False

    def update_title(self, conversation_id: int, title: str) -> None:
        conv = self._db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.title = title
            self._db.commit()

    async def extract_insights(
        self, conversation_id: int, user_id: int, model: str | None = None
    ) -> builtins.list[dict]:
        try:
            from backend.app.services.intelligence.llm.manager import llm_manager
            from backend.app.services.intelligence.llm.provider import LLMMessage
            from backend.app.services.memory.long_term import LongTermMemoryService

            messages = self.get_messages(conversation_id, limit=50)
            if len(messages) < 2:
                return []

            conversation_text = "\n".join(f"{m.role}: {m.content}" for m in messages)  # type: ignore[attr-defined]
            extraction_prompt = (
                "Analyze this conversation and extract key insights about the user. "
                "For each insight, provide:\n"
                "- category: one of preference, pattern, fact, context\n"
                "- title: short title (max 50 chars)\n"
                "- content: the insight (max 200 chars)\n\n"
                "Return a JSON array of insights. Only include meaningful, actionable insights. "
                "If no insights can be extracted, return an empty array [].\n\n"
                f"Conversation:\n{conversation_text}"
            )

            llm_messages = [
                LLMMessage(role="system", content="You are an insight extraction assistant. Return ONLY valid JSON."),
                LLMMessage(role="user", content=extraction_prompt),
            ]
            result = await llm_manager.chat(llm_messages, model=model, max_tokens=1024, temperature=0.3)

            import json
            import re

            raw = result.content.strip()
            json_match = re.search(r"\[.*\]", raw, re.DOTALL)
            if not json_match:
                return []
            insights = json.loads(json_match.group())

            svc = LongTermMemoryService(self._db)
            stored = []
            for insight in insights:
                if not isinstance(insight, dict):
                    continue
                category = insight.get("category", "fact")
                if category not in ("preference", "pattern", "fact", "context"):
                    category = "fact"
                title = str(insight.get("title", ""))[:50]
                content = str(insight.get("content", ""))[:200]
                if not title or not content:
                    continue
                memory = svc.create(
                    user_id=user_id,
                    category=category,
                    title=title,
                    content=content,
                    source="conversation",
                    source_id=conversation_id,
                )
                stored.append({"id": memory.id, "category": category, "title": title})
            return stored
        except Exception as e:
            logger.warning("Failed to extract insights: %s", e)
            return []

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
