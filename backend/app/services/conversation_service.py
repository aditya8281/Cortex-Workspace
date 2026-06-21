from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models.conversation import Conversation, ConversationMessage

# Approximate tokens per character (English text ~4 chars per token)
CHARS_PER_TOKEN = 4

# Context window: max tokens to keep in history
MAX_CONTEXT_TOKENS = 32000


def estimate_tokens(text: str) -> int:
    """Approximate token count from text length."""
    return max(1, len(text) // CHARS_PER_TOKEN)


class ConversationService:
    def __init__(self, db: Session):
        self._db = db

    def create(
        self, user_id: int, title: str = "New Conversation", repo_id: int | None = None
    ) -> Conversation:
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
        conv = (
            self._db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if conv:
            conv.message_count = (conv.message_count or 0) + 1
            conv.total_tokens = (conv.total_tokens or 0) + tokens
        self._db.commit()
        self._db.refresh(msg)
        return msg

    def get_messages(self, conversation_id: int, limit: int = 50) -> list[ConversationMessage]:
        return (
            self._db.query(ConversationMessage)
            .filter(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
            .limit(limit)
            .all()
        )

    def get_context_messages(
        self, conversation_id: int, max_tokens: int = MAX_CONTEXT_TOKENS
    ) -> list[ConversationMessage]:
        """Get messages that fit within the token budget, keeping most recent."""
        all_msgs = self.get_messages(conversation_id, limit=500)
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
        conv = (
            self._db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if conv:
            conv.title = title
            self._db.commit()

    async def generate_title(self, content: str, model: str | None = None) -> str:
        try:
            from backend.app.services.llm.manager import llm_manager
            from backend.app.services.llm.provider import LLMMessage

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
            pass
        return content[:50].strip()
