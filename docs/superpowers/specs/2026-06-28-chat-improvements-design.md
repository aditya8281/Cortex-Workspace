Last updated: 2026-06-28

# Chat Improvements Design Spec

## Overview

Targeted improvements to the existing Chat page: conversation management (rename/delete), message display (code blocks, timestamps, sources panel), and input enhancements (keyboard shortcuts, context hints).

## Current State

The Chat page already has:
- ✅ Conversation sidebar with list
- ✅ New conversation creation
- ✅ Message display with streaming
- ✅ Model selector dropdown
- ✅ Sources display
- ✅ Auto-scroll to bottom

## Improvements

### 1. Conversation Management

**Rename:**
- Double-click conversation title in sidebar → inline edit
- Enter to save, Escape to cancel
- Calls `PATCH /conversations/{id}/title`

**Delete:**
- Hover conversation → trash icon appears
- Click → confirmation tooltip ("Delete this conversation?")
- Calls `DELETE /conversations/{id}`
- If deleted conversation was active, clear active state

### 2. Message Display

**Code Blocks:**
- Detect markdown code blocks (```...```)
- Render with JetBrains Mono font
- Copy button on hover
- Language badge (if detected)

**Timestamps:**
- Show relative time under each message ("2 minutes ago", "1 hour ago")
- Full timestamp on hover (title attribute)

**Sources Panel:**
- Collapsible panel below messages
- Shows file path, score, content snippet
- Click to expand full content

### 3. Input Enhancements

**Keyboard Shortcuts:**
- Enter to send (already works)
- Shift+Enter for newline
- Ctrl+K to focus model selector
- Escape to close new conversation modal

**Context Hints:**
- Show current model name below input
- Show conversation title in header
- Message count indicator

### 4. Empty States

**No conversations:**
- Illustration + "Start a conversation" message
- "New Chat" button prominent

**No messages in conversation:**
- "Send a message to get started"
- Model selector visible

## Components

```
frontend/src/features/chat/
├── page.tsx                    # MODIFY: add rename/delete, code blocks, shortcuts
├── components/
│   ├── CodeBlock.tsx           # NEW: syntax-highlighted code with copy
│   ├── ConversationItem.tsx    # NEW: single conversation with rename/delete
│   ├── SourcesPanel.tsx        # NEW: collapsible sources display
│   └── MessageBubble.tsx       # NEW: message with timestamp + code blocks
```

## Files

| Action | File |
|--------|------|
| Modify | `features/chat/page.tsx` — add rename/delete, wire new components |
| Create | `features/chat/components/CodeBlock.tsx` |
| Create | `features/chat/components/ConversationItem.tsx` |
| Create | `features/chat/components/SourcesPanel.tsx` |
| Create | `features/chat/components/MessageBubble.tsx` |
| **Total** | **4 created, 1 modified** |

## Anti-Slop

- No transition-all
- Code blocks: solid background, no glassmorphism
- Timestamps: text-text-muted, not decorative
- Copy button: minimal, appears on hover only
