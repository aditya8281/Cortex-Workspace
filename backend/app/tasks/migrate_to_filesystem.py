"""Migration script: Copy existing DB data to filesystem.

Run once to populate {storage_root}/conversations/, {storage_root}/memory/
from the existing Postgres tables.

Usage:
    .venv/bin/python -m backend.app.tasks.migrate_to_filesystem

Or import and call:
    from backend.app.tasks.migrate_to_filesystem import migrate_all
    migrate_all(db)
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def migrate_conversations(db: Session, ws, user_id: int) -> int:
    """Migrate all conversations for a user from DB to filesystem."""
    from backend.app.models.interaction.conversation import Conversation, ConversationMessage

    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .all()
    )
    count = 0
    for conv in conversations:
        try:
            ws.conversations.index_entry(
                conv.id, title=conv.title or "",
                model_used=conv.model_used,
            )
            messages = (
                db.query(ConversationMessage)
                .filter(ConversationMessage.conversation_id == conv.id)
                .order_by(ConversationMessage.created_at)
                .all()
            )
            for msg in messages:
                ws.conversations.append_message(
                    conv.id, msg.role, msg.content,
                    tokens=msg.tokens or 0,
                    thinking_content=getattr(msg, "thinking_content", None),
                )
            count += 1
        except Exception as exc:
            logger.warning("Failed to migrate conv %d: %s", conv.id, exc)
    return count


def migrate_memories(db: Session, ws, user_id: int) -> int:
    """Migrate long-term memories from DB to filesystem."""
    from backend.app.models.memory.long_term_memory import LongTermMemory

    memories = (
        db.query(LongTermMemory)
        .filter(LongTermMemory.user_id == user_id)
        .all()
    )
    count = 0
    for mem in memories:
        try:
            ws.memory.add_memory(
                category=mem.category,
                title=mem.title,
                content=mem.content,
                confidence=mem.confidence,
                source=mem.source or "",
                source_id=mem.source_id,
            )
            count += 1
        except Exception as exc:
            logger.warning("Failed to migrate memory %d: %s", mem.id, exc)
    return count


def migrate_user(db: Session, user_id: int) -> dict:
    """Migrate all data for a single user from DB to filesystem."""
    from backend.app.services.storage.factory import get_user_workspace

    ws = get_user_workspace(user_id, db)
    result = {"user_id": user_id, "conversations": 0, "memories": 0}

    try:
        result["conversations"] = migrate_conversations(db, ws, user_id)
    except Exception as exc:
        logger.error("Conversation migration failed for user %d: %s", user_id, exc)

    try:
        result["memories"] = migrate_memories(db, ws, user_id)
    except Exception as exc:
        logger.error("Memory migration failed for user %d: %s", user_id, exc)

    return result


def migrate_all(db: Session) -> list[dict]:
    """Migrate all users from DB to filesystem."""
    from backend.app.models.auth.user import User

    users = db.query(User).all()
    results = []
    for user in users:
        logger.info("Migrating user %d (%s)...", user.id, user.username)
        result = migrate_user(db, user.id)
        results.append(result)
        logger.info(
            "User %d: %d conversations, %d memories migrated",
            user.id, result["conversations"], result["memories"],
        )
    return results


def migrate_single(db: Session, user_id: int) -> dict:
    """Migrate a single user by ID."""
    return migrate_user(db, user_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        results = migrate_all(db)
        total_convs = sum(r["conversations"] for r in results)
        total_mems = sum(r["memories"] for r in results)
        print(
            f"\nMigration complete: {len(results)} users, "
            f"{total_convs} conversations, {total_mems} memories"
        )
    finally:
        db.close()
