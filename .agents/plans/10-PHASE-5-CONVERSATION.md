# Phase 5: Conversation & Context

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Persistent conversations with context. Cortex remembers what you discussed, builds context from your workspace, and maintains conversation history across sessions.

**Architecture:** Conversation storage in PostgreSQL, streaming chat via SSE, token-aware context window management, conversation history with search.

**Tech Stack:** Python 3.12+, SQLAlchemy 2.0, Alembic, Next.js 15, React 19

---

## Task 1: Conversation Models & Storage

**Files:**
- Create: `backend/app/models/conversation.py`
- Create: `backend/app/services/conversation_service.py`
- Create migration: `q00000000017_add_conversations.py`

- [ ] **Step 1: Create Conversation and ConversationMessage models**

```python
# backend/app/models/conversation.py
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), server_default="New Conversation")
    repo_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, server_default="0")
    total_tokens: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "system", "user", "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
```

- [ ] **Step 2: Create Alembic migration**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run alembic revision -m "add conversations tables" --head=o00000000015
```

Write migration `migrations/versions/q00000000017_add_conversations.py`:

```python
"""add conversations tables

Revision ID: q00000000017
Revises: o00000000015
"""
from alembic import op
import sqlalchemy as sa

revision = "q00000000017"
down_revision = "o00000000015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("title", sa.String(255), server_default="New Conversation"),
        sa.Column("repo_id", sa.Integer, nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("message_count", sa.Integer, server_default="0"),
        sa.Column("total_tokens", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "conversation_id",
            sa.Integer,
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("conversation_messages")
    op.drop_table("conversations")
```

- [ ] **Step 3: Run migration**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run alembic upgrade head
```

- [ ] **Step 4: Create ConversationService**

```python
# backend/app/services/conversation_service.py
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
```

- [ ] **Step 5: Compile check**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run python -m py_compile backend/app/models/conversation.py && uv run python -m py_compile backend/app/services/conversation_service.py && echo "PASS"
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/conversation.py backend/app/services/conversation_service.py migrations/versions/q00000000017_add_conversations.py
git commit -m "feat: conversation models, service, and migration"
```

---

## Task 2: Conversation API & Streaming Chat Endpoint

**Files:**
- Create: `backend/app/api/v1/conversations.py`
- Modify: `backend/app/api/router.py` (register router)

- [ ] **Step 1: Create conversation API with SSE streaming chat**

```python
# backend/app/api/v1/conversations.py
from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
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
) -> AsyncGenerator[str, None]:
    """Generator that yields SSE events for the chat response."""
    from backend.app.services.llm.manager import llm_manager
    from backend.app.services.llm.provider import LLMMessage

    svc = ConversationService(db)

    # Save user message with token count
    user_tokens = estimate_tokens(user_content)
    svc.add_message(conversation_id, "user", user_content, tokens=user_tokens)

    # Build context from conversation history (token-budget aware)
    history = svc.get_context_messages(conversation_id)
    messages = [LLMMessage(role=m.role, content=m.content) for m in history]

    full_response = ""
    response_tokens = 0

    try:
        async for chunk in llm_manager.chat_stream(messages, max_tokens=2048, temperature=0.7):
            full_response += chunk
            response_tokens = estimate_tokens(full_response)
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'tokens': response_tokens})}\n\n"
    except RuntimeError as e:
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
        _stream_chat_response(conversation_id, payload.content, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 2: Register router**

In `backend/app/api/router.py`, add the import and include:

```python
from backend.app.api.v1.conversations import router as conversations_router
# ... after existing includes:
api_router.include_router(conversations_router, tags=["Conversations"])
```

- [ ] **Step 3: Compile check**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run python -m py_compile backend/app/api/v1/conversations.py && echo "PASS"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/conversations.py backend/app/api/router.py
git commit -m "feat: conversation API with CRUD and SSE streaming chat endpoint"
```

---

## Task 3: Chat UI

**Files:**
- Create: `frontend/app/chat/page.tsx`
- Modify: `frontend/src/shared/layout/DashboardShell.tsx` (add Chat nav item)

- [ ] **Step 1: Create chat page with streaming support**

```tsx
// frontend/app/chat/page.tsx
"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Plus, MessageSquare, Trash2, Send } from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import Card from "@/shared/ui/Card";
import { useAuth } from "@/shared/auth/AuthProvider";
import { api } from "@/shared/api/client";

interface Message {
  role: string;
  content: string;
  tokens?: number;
  created_at: string;
}

interface Conversation {
  id: number;
  title: string;
  message_count: number;
  total_tokens: number;
  updated_at: string;
}

export default function ChatPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const messagesEnd = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!loading && !user) router.replace("/auth");
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    api.get<{ conversations: Conversation[] }>("/api/v1/conversations").then((data) => {
      setConversations(data.conversations);
      if (data.conversations.length > 0 && !activeId) {
        setActiveId(data.conversations[0].id);
      }
    });
  }, [user]);

  useEffect(() => {
    if (!activeId) return;
    api.get<{ messages: Message[] }>(`/api/v1/conversations/${activeId}`).then((data) => {
      setMessages(data.messages);
    });
  }, [activeId]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const createConversation = async () => {
    const data = await api.post<{ id: number }>("/api/v1/conversations", {
      title: "New Conversation",
    });
    setConversations((prev) => [
      {
        id: data.id,
        title: "New Conversation",
        message_count: 0,
        total_tokens: 0,
        updated_at: new Date().toISOString(),
      },
      ...prev,
    ]);
    setActiveId(data.id);
    setMessages([]);
  };

  const sendMessage = useCallback(async () => {
    if (!input.trim() || !activeId || sending) return;

    const userMsg: Message = {
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);
    setStreamingContent("");

    try {
      const res = await fetch(`/api/v1/conversations/${activeId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: userMsg.content }),
        signal: abortRef.current?.signal,
      });

      if (!res.ok) throw new Error("Failed to send message");

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === "chunk") {
              setStreamingContent((prev) => prev + event.content);
            } else if (event.type === "done") {
              setMessages((prev) => [
                ...prev,
                {
                  role: "assistant",
                  content: streamingContent || event.content || "",
                  tokens: event.total_tokens,
                  created_at: new Date().toISOString(),
                },
              ]);
              setStreamingContent("");
            }
          } catch {
            // skip malformed SSE lines
          }
        }
      }
    } catch (err: any) {
      if (err.name === "AbortError") return;
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Failed to get response. Please try again.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
      setStreamingContent("");
    }
  }, [input, activeId, sending, streamingContent]);

  const deleteConversation = async (id: number) => {
    await api.delete(`/api/v1/conversations/${id}`);
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) {
      setActiveId(conversations.find((c) => c.id !== id)?.id ?? null);
    }
  };

  if (loading || !user) return null;

  return (
    <DashboardShell>
      <div className="relative z-10 flex h-[calc(100vh-4rem)]">
        {/* Sidebar */}
        <div className="w-64 border-r border-border-subtle p-4 flex flex-col">
          <button
            onClick={createConversation}
            className="w-full py-2 rounded-lg bg-accent/10 text-accent text-sm font-medium hover:bg-accent/20 transition-colors flex items-center justify-center gap-2 mb-4"
          >
            <Plus size={14} /> New Chat
          </button>
          <div className="flex-1 overflow-y-auto space-y-1">
            {conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => setActiveId(c.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors group ${
                  activeId === c.id
                    ? "bg-bg-hover text-text"
                    : "text-text-secondary hover:bg-bg-hover/50"
                }`}
              >
                <MessageSquare size={14} />
                <span className="flex-1 truncate text-sm">{c.title}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(c.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 text-text-muted hover:text-danger"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && !streamingContent && (
              <div className="flex items-center justify-center h-full">
                <p className="text-text-muted text-sm">
                  Start a conversation with Cortex.
                </p>
              </div>
            )}
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <Card
                  className={`max-w-2xl px-4 py-3 text-sm ${
                    msg.role === "user" ? "bg-accent/10 border-accent/20" : ""
                  }`}
                >
                  <p className="text-text whitespace-pre-wrap">{msg.content}</p>
                  {msg.tokens && (
                    <p className="text-[10px] text-text-muted mt-1">
                      {msg.tokens} tokens
                    </p>
                  )}
                </Card>
              </motion.div>
            ))}
            {sending && streamingContent && (
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <Card className="max-w-2xl px-4 py-3 text-sm">
                  <p className="text-text whitespace-pre-wrap">{streamingContent}</p>
                  <div className="flex items-center gap-1 mt-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                  </div>
                </Card>
              </motion.div>
            )}
            {sending && !streamingContent && (
              <div className="flex justify-start">
                <Card className="px-4 py-3 text-sm">
                  <div className="flex items-center gap-2 text-text-muted">
                    <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                    Thinking...
                  </div>
                </Card>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-border-subtle">
            <div className="flex gap-2 max-w-3xl mx-auto">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Ask Cortex anything..."
                className="flex-1 bg-bg-surface border border-border-subtle rounded-lg px-4 py-3 text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors"
                disabled={sending}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || sending}
                className="px-4 py-3 rounded-lg bg-accent text-bg font-medium hover:bg-accent-bright transition-colors disabled:opacity-50"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
```

- [ ] **Step 2: Add Chat to DashboardShell**

In `frontend/src/shared/layout/DashboardShell.tsx`, add `MessageSquare` to the lucide-react import and add Chat to the work nav:

```tsx
// Add to lucide-react imports:
import { ..., MessageSquare } from "lucide-react";

// Add to workNavItems array (after Agents):
{ label: "Chat", href: "/chat", icon: MessageSquare },
```

- [ ] **Step 3: Build check**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend && npx next build 2>&1 | tail -15
```

- [ ] **Step 4: Commit**

```bash
git add frontend/app/chat/ frontend/src/shared/layout/DashboardShell.tsx
git commit -m "feat: chat UI with streaming SSE support and token display"
```

---

## Exit Criteria

- [ ] Conversations stored in PostgreSQL with full message history
- [ ] Token counting per message (`len(content) // 4` approximation)
- [ ] Context window management (truncates old messages at 32k token budget)
- [ ] CRUD API for conversations (list, create, get, delete)
- [ ] Streaming SSE chat endpoint using `llm_manager.chat_stream()`
- [ ] Fallback message when LLM is not available
- [ ] Chat UI with sidebar, streaming message bubbles, and token counts
- [ ] Conversation history persists across sessions
- [ ] All code compiles and builds clean
