Last updated: 2026-06-28

# Chat Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance existing Chat page — conversation rename/delete, code block rendering, timestamps, sources panel, keyboard shortcuts.

**Architecture:** Add new components alongside existing chat/page.tsx. Wire into existing conversation/message flow.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS, existing shared UI.

## Global Constraints

- Dark-only. All colors from DESIGN.md tokens.
- JetBrains Mono for code blocks. Geist for everything else.
- No `transition-all`, `h-screen`, gradient text, glassmorphism.
- Copy button on code blocks: hover-only, minimal.
- Timestamps: `text-text-muted`, `font-mono`, relative format.

## Existing Chat State

- `features/chat/page.tsx` — main chat page with conversations sidebar and message area
- `features/chat/api.ts` — API client with conversation CRUD and streaming
- Conversations listed in left sidebar with "New Chat" button
- Messages rendered with user/assistant roles

## Chat API Endpoints Available

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat/conversations` | GET | List conversations |
| `/chat/conversations` | POST | Create conversation |
| `/chat/conversations/{id}` | GET | Get conversation |
| `/chat/conversations/{id}/title` | PATCH | Update title |
| `/chat/conversations/{id}` | DELETE | Delete conversation |
| `/chat/conversations/{id}/messages` | GET | Get messages |
| `/chat/completions` | POST | Send message (SSE) |
| `/chat/models` | GET | Available models |
| `/chat/sources` | GET | RAG sources for a message |

---

### Task 1: CodeBlock Component

**Files:**
- Create: `frontend/src/features/chat/components/CodeBlock.tsx`

- [ ] **Step 1: Create CodeBlock component**

```tsx
"use client";

import { useState } from "react";

interface CodeBlockProps {
  language?: string;
  children: string;
}

export function CodeBlock({ language, children }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="group relative my-3 rounded-lg border border-border-subtle bg-bg-surface overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-bg-elevated border-b border-border-subtle">
        {language ? (
          <span className="text-[10px] text-text-muted uppercase tracking-wide">{language}</span>
        ) : (
          <span />
        )}
        <button
          onClick={handleCopy}
          className="text-[10px] text-text-muted hover:text-text-secondary opacity-0 group-hover:opacity-100 transition-opacity duration-150 cursor-pointer"
          aria-label="Copy code"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>

      {/* Code */}
      <pre className="p-3 overflow-x-auto text-xs leading-relaxed">
        <code className="text-text-secondary font-mono">{children}</code>
      </pre>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/chat/components/CodeBlock.tsx
git commit -m "feat(chat): add CodeBlock component with syntax badge and copy"
```

---

### Task 2: MessageBubble Component

**Files:**
- Create: `frontend/src/features/chat/components/MessageBubble.tsx`

- [ ] **Step 1: Create MessageBubble with timestamps and code block detection**

```tsx
"use client";

import { useMemo } from "react";
import { CodeBlock } from "./CodeBlock";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  sources?: Array<{ title: string; path: string; score: number; snippet: string }>;
}

function relativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function parseContent(content: string): Array<{ type: "text" | "code"; content: string; language?: string }> {
  const parts: Array<{ type: "text" | "code"; content: string; language?: string }> = [];
  const regex = /```(\w+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;

  let match;
  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", content: content.slice(lastIndex, match.index) });
    }
    parts.push({ type: "code", language: match[1] || undefined, content: match[2].trim() });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    parts.push({ type: "text", content: content.slice(lastIndex) });
  }

  if (parts.length === 0) {
    parts.push({ type: "text", content });
  }

  return parts;
}

export function MessageBubble({ role, content, timestamp, sources }: MessageBubbleProps) {
  const parts = useMemo(() => parseContent(content), [content]);

  return (
    <div className={`flex flex-col ${role === "user" ? "items-end" : "items-start"}`} role="article" aria-label={`${role} message`}>
      <div
        className={`max-w-[85%] rounded-xl px-4 py-2.5 ${
          role === "user"
            ? "bg-accent/15 text-text-primary"
            : "bg-bg-elevated text-text-primary border border-border-subtle"
        }`}
      >
        {parts.map((part, i) => {
          if (part.type === "code") {
            return <CodeBlock key={i} language={part.language}>{part.content}</CodeBlock>;
          }
          // Split text into paragraphs
          return part.content.split("\n\n").filter(Boolean).map((para, j) => (
            <p key={`${i}-${j}`} className="text-sm leading-relaxed whitespace-pre-wrap">{para}</p>
          ));
        })}
      </div>

      {/* Timestamp */}
      {timestamp && (
        <span
          className="text-[10px] text-text-muted font-mono mt-1 px-1"
          title={new Date(timestamp).toLocaleString()}
        >
          {relativeTime(timestamp)}
        </span>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/chat/components/MessageBubble.tsx
git commit -m "feat(chat): add MessageBubble with timestamps and code block parsing"
```

---

### Task 3: ConversationItem + SourcesPanel

**Files:**
- Create: `frontend/src/features/chat/components/ConversationItem.tsx`
- Create: `frontend/src/features/chat/components/SourcesPanel.tsx`

- [ ] **Step 1: Create ConversationItem with rename/delete**

```tsx
"use client";

import { useState, useRef, useEffect } from "react";

interface ConversationItemProps {
  id: string;
  title: string;
  isActive: boolean;
  onSelect: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}

export function ConversationItem({ id, title, isActive, onSelect, onRename, onDelete }: ConversationItemProps) {
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(title);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const handleSave = () => {
    if (editTitle.trim()) {
      onRename(id, editTitle.trim());
    } else {
      setEditTitle(title);
    }
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSave();
    if (e.key === "Escape") {
      setEditTitle(title);
      setEditing(false);
    }
  };

  const handleDelete = () => {
    onDelete(id);
    setShowDeleteConfirm(false);
  };

  return (
    <div
      className={`group flex items-center justify-between gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors duration-150 ${
        isActive ? "bg-bg-hover text-text-primary" : "text-text-secondary hover:bg-bg-hover/50"
      }`}
      onClick={() => !editing && onSelect(id)}
    >
      {editing ? (
        <input
          ref={inputRef}
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-bg-surface border border-border-default rounded px-2 py-0.5 text-xs text-text-primary focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none"
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <span className="flex-1 truncate text-xs">{title}</span>
      )}

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150 flex-shrink-0">
        {!editing && (
          <>
            <button
              onClick={(e) => { e.stopPropagation(); setEditing(true); }}
              className="p-0.5 text-text-muted hover:text-text-secondary cursor-pointer"
              aria-label="Rename conversation"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.2">
                <path d="M10 1.5l2.5 2.5L4.5 12H2v-2.5L10 1.5z" />
              </svg>
            </button>
            <div className="relative">
              <button
                onClick={(e) => { e.stopPropagation(); setShowDeleteConfirm(!showDeleteConfirm); }}
                className="p-0.5 text-text-muted hover:text-danger cursor-pointer"
                aria-label="Delete conversation"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.2">
                  <path d="M2 3.5h10M5 3.5V2.5a1 1 0 011-1h2a1 1 0 011 1v1M3.5 3.5l.5 8a1 1 0 001 1h4a1 1 0 001-1l.5-8" />
                </svg>
              </button>
              {showDeleteConfirm && (
                <div className="absolute right-0 top-full mt-1 z-10 bg-bg-elevated border border-border-subtle rounded-lg p-2 shadow-lg" onClick={(e) => e.stopPropagation()}>
                  <p className="text-[10px] text-text-muted mb-1.5">Delete this?</p>
                  <div className="flex gap-1.5">
                    <button onClick={handleDelete} className="text-[10px] text-danger hover:underline cursor-pointer">Yes</button>
                    <button onClick={() => setShowDeleteConfirm(false)} className="text-[10px] text-text-muted hover:underline cursor-pointer">No</button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create SourcesPanel**

```tsx
"use client";

import { useState } from "react";

interface Source {
  title: string;
  path: string;
  score: number;
  snippet: string;
}

interface SourcesPanelProps {
  sources: Source[];
}

export function SourcesPanel({ sources }: SourcesPanelProps) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="border-t border-border-subtle mt-4 pt-3">
      <button
        onClick={() => setExpanded(expanded === null ? 0 : null)}
        className="flex items-center gap-2 text-xs text-text-muted hover:text-text-secondary transition-colors duration-150 cursor-pointer"
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.2">
          <path d="M2 2h8v8H2z" />
          <path d="M4 6h4M4 4h4M4 8h2" />
        </svg>
        {sources.length} source{sources.length !== 1 ? "s" : ""}
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.2" className={`transition-transform duration-150 ${expanded !== null ? "rotate-180" : ""}`}>
          <path d="M2 3.5l3 3 3-3" />
        </svg>
      </button>

      {expanded !== null && (
        <div className="mt-2 space-y-2 max-h-60 overflow-y-auto">
          {sources.map((source, i) => (
            <div key={i} className="p-2 rounded-md bg-bg-surface border border-border-subtle">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-text-secondary font-mono truncate">{source.path}</span>
                <span className="text-[10px] text-text-muted">{Math.round(source.score * 100)}%</span>
              </div>
              <p className="text-[10px] text-text-muted line-clamp-2">{source.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/chat/components/ConversationItem.tsx frontend/src/features/chat/components/SourcesPanel.tsx
git commit -m "feat(chat): add ConversationItem with rename/delete and SourcesPanel"
```

---

### Task 4: Wire Improvements into Chat Page

**Files:**
- Modify: `frontend/src/features/chat/page.tsx`

- [ ] **Step 1: Read current chat page to understand structure**

Read `frontend/src/features/chat/page.tsx` and understand:
- How conversations are rendered in sidebar
- How messages are rendered
- Where to add ConversationItem, MessageBubble, SourcesPanel

- [ ] **Step 2: Update imports and conversation rendering**

Replace the conversation list rendering to use `ConversationItem`:

```tsx
import { ConversationItem } from "./components/ConversationItem";
import { MessageBubble } from "./components/MessageBubble";
import { SourcesPanel } from "./components/SourcesPanel";
```

In the conversations sidebar, replace the plain conversation list items:

```tsx
{conversations.map((conv) => (
  <ConversationItem
    key={conv.id}
    id={conv.id}
    title={conv.title}
    isActive={activeConvId === conv.id}
    onSelect={(id) => { setActiveConvId(id); loadConversation(id); }}
    onRename={(id, title) => {
      chatApi.renameConversation(id, title);
      setConversations((prev) => prev.map((c) => c.id === id ? { ...c, title } : c));
    }}
    onDelete={(id) => {
      chatApi.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConvId === id) setActiveConvId(null);
    }}
  />
))}
```

- [ ] **Step 3: Update message rendering**

Replace the message rendering section to use `MessageBubble`:

```tsx
{messages.map((msg, i) => (
  <div key={i} className="px-4">
    <MessageBubble
      role={msg.role as "user" | "assistant"}
      content={msg.content}
      timestamp={msg.timestamp}
      sources={msg.sources}
    />
    {msg.sources && i === messages.length - 1 && (
      <div className="px-4">
        <SourcesPanel sources={msg.sources} />
      </div>
    )}
  </div>
))}
```

- [ ] **Step 4: Add keyboard shortcut for Escape**

Add to the chat page component:

```tsx
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      setShowNewConvModal(false);
    }
    // Ctrl+K for model selector
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      modelSelectorRef.current?.focus();
    }
  };
  document.addEventListener("keydown", handleKeyDown);
  return () => document.removeEventListener("keydown", handleKeyDown);
}, []);
```

- [ ] **Step 5: Add model name display below input**

After the chat input area:

```tsx
{selectedModel && (
  <div className="flex items-center gap-1.5 px-4 pb-2">
    <span className="text-[10px] text-text-muted">Model: </span>
    <span className="text-[10px] text-text-secondary">{selectedModel}</span>
  </div>
)}
```

- [ ] **Step 6: Add empty states**

For no conversations:
```tsx
{conversations.length === 0 && (
  <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
    <p className="text-sm text-text-muted mb-3">Start a conversation</p>
    <Button size="sm" onClick={handleNewChat}>New Chat</Button>
  </div>
)}
```

For no messages in conversation:
```tsx
{messages.length === 0 && activeConvId && (
  <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
    <p className="text-sm text-text-muted">Send a message to get started</p>
  </div>
)}
```

- [ ] **Step 7: Build + commit**

```bash
cd frontend && npm run build 2>&1 | grep -E 'Compiled|error|Failed'
git add frontend/src/features/chat/page.tsx
git commit -m "feat(chat): wire CodeBlock, MessageBubble, ConversationItem, SourcesPanel into chat page"
```

---

### Task 5: Final Build Validation

- [ ] **Step 1: Full build**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

- [ ] **Step 2: Verify keyboard shortcuts**

```bash
grep -n 'Escape\|ctrlKey\|metaKey' frontend/src/features/chat/page.tsx
```

- [ ] **Step 3: Verify empty states**

```bash
grep -n 'Start a conversation\|Send a message' frontend/src/features/chat/page.tsx
```

- [ ] **Step 4: Verify no forbidden patterns**

```bash
grep -rn 'transition-all\|h-screen\|gradient.*text' frontend/src/features/chat/components/ --include='*.tsx'
```

---

## Summary

| Task | What It Builds | Files |
|------|---------------|-------|
| 1 | CodeBlock with copy + language badge | 1 created |
| 2 | MessageBubble with timestamps + code parsing | 1 created |
| 3 | ConversationItem with rename/delete + SourcesPanel | 2 created |
| 4 | Wire improvements into chat page | 1 modified |
| 5 | Final validation | 0 |
| **Total** | | **4 created, 1 modified** |
