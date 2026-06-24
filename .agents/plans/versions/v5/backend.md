# V5 Backend: The Workspace

## Overview

V5 transforms Cortex from a brain into a complete workspace. Email, calendar, tasks, notes, documents, and contacts all integrated with the agent. OpenAI-compatible API makes Cortex accessible to any tool. Cross-tool workflows create a unified productivity experience.

## File Structure (V5 additions)

```
backend/app/
├── services/
│   ├── integrations/          # NEW: External integrations (V5 Phase 1)
│   │   ├── __init__.py
│   │   ├── oauth.py           # OAuth 2.0 flow manager
│   │   ├── email/
│   │   │   ├── __init__.py
│   │   │   ├── base.py        # Protocol[EmailProvider]
│   │   │   ├── gmail.py       # Gmail API
│   │   │   ├── outlook.py     # Outlook API
│   │   │   ├── cache.py       # Local email cache
│   │   │   └── digest.py      # Email digest generator
│   │   └── calendar/
│   │       ├── __init__.py
│   │       ├── base.py        # Protocol[CalendarProvider]
│   │       ├── google.py      # Google Calendar API
│   │       ├── outlook.py     # Outlook Calendar API
│   │       └── cache.py       # Local calendar cache
│   ├── tasks/                 # NEW: Task management (V5 Phase 2)
│   │   ├── __init__.py
│   │   ├── manager.py         # Task CRUD + lifecycle
│   │   ├── reminder.py        # Reminder system
│   │   └── views.py           # Task views (today, upcoming, overdue)
│   ├── notes/                 # NEW: Notes system (V5 Phase 2)
│   │   ├── __init__.py
│   │   ├── manager.py         # Note CRUD + lifecycle
│   │   ├── parser.py          # Markdown parser + frontmatter
│   │   └── linker.py          # Wiki-link resolution
│   ├── documents/             # NEW: Document management (V5 Phase 2)
│   │   ├── __init__.py
│   │   ├── manager.py         # Document lifecycle
│   │   ├── parser.py          # Multi-format parsing
│   │   ├── chunker.py         # Smart chunking
│   │   └── indexer.py         # Vector + fulltext indexing
│   ├── contacts/              # NEW: Contacts (V5 Phase 3)
│   │   ├── __init__.py
│   │   ├── manager.py         # Contact CRUD
│   │   ├── resolver.py        # Entity resolution
│   │   └── enricher.py        # Auto-enrichment
│   ├── api_compat/            # NEW: OpenAI-compatible API (V5 Phase 3)
│   │   ├── __init__.py
│   │   ├── chat.py            # /v1/chat/completions
│   │   ├── models.py          # /v1/models
│   │   ├── middleware.py      # API key auth + rate limiting
│   │   └── usage.py           # Usage tracking
│   └── workspace/             # NEW: Workspace unification (V5 Phase 3)
│       ├── __init__.py
│       ├── dashboard.py       # Unified workspace dashboard
│       └── crossref.py        # Cross-tool linking
├── models/
│   ├── task.py                # NEW
│   ├── note.py                # NEW
│   ├── document.py            # NEW (or extend existing)
│   ├── contact.py             # NEW
│   ├── integration.py         # NEW
│   └── api_key.py             # NEW
├── api/v1/
│   ├── integrations.py        # NEW
│   ├── tasks.py               # NEW
│   ├── notes.py               # NEW
│   ├── documents.py           # NEW
│   ├── contacts.py            # NEW
│   ├── openai_compat.py       # NEW
│   └── workspace.py           # NEW
└── migrations/
    └── versions/
        ├── d00000000009_integrations.py      # Email + calendar
        ├── d00000000010_tasks_notes_docs.py  # Tasks + notes + documents
        └── d00000000011_contacts_api.py      # Contacts + API keys
```

## Phase 1: Email + Calendar

### OAuth Providers

| Provider | Auth URL | Scopes |
|----------|----------|--------|
| Gmail | accounts.google.com | gmail.readonly, gmail.send, calendar |
| Outlook | login.microsoftonline.com | Mail.Read, Mail.Send, Calendars.ReadWrite |

### Local Caching Strategy

All data cached locally for offline access:
- Email: full body encrypted, metadata indexed
- Calendar: full event data, recurring event expansion
- Sync interval: configurable (5/15/30/60 min)
- Cache invalidation: webhook push (Gmail/Outlook push notifications)

### Security

- OAuth tokens encrypted with user's vault key
- Tokens never sent to external services (only to provider APIs)
- Local cache encrypted at rest
- Clear data policy: what's cached, how long, how to delete

## Phase 2: Tasks + Notes + Documents

### Task System

4 statuses: pending, in_progress, completed, cancelled
4 priorities: low, medium, high, urgent
Features: subtasks, tags, due dates, reminders, source tracking

### Notes System

Markdown with frontmatter support:
```markdown
---
title: Memory Architecture Comparison
tags: [architecture, memory]
source: research
---

# Memory Architecture Comparison

Comparing [[mem0]] and [[graphiti]] approaches...
```

Wiki-link resolution: [[note title]] → link to note. Bidirectional linking.

### Document Management

Supported formats:
- PDF (via PyMuPDF or pdfplumber)
- DOCX (via python-docx)
- Markdown (native)
- TXT (plain text)
- HTML (via BeautifulSoup)
- CSV (via pandas)

Smart chunking: paragraph-aware, overlap for context, metadata preserved.

## Phase 3: Contacts + OpenAI API + Workspace

### Contact Resolution

Auto-link contacts from:
- Email senders/recipients
- Calendar event attendees
- Task mentions in descriptions
- Document authorship

### OpenAI-Compatible API

Endpoints:
- `POST /v1/chat/completions` — chat completions
- `GET /v1/models` — list available models
- `POST /v1/embeddings` — text embeddings (future)

Authentication: Bearer token (API key)
Rate limiting: per-key, configurable
Usage tracking: tokens, latency, endpoint

### Workspace Dashboard

Unified view across all tools:
- Email summary (unread, urgent)
- Calendar (today's events)
- Tasks (today, overdue)
- Notes (recent)
- Documents (recent)
- Contacts (recent)
- Agent (status, recent runs)

## Testing Strategy

| Test Category | Count Target | Approach |
|--------------|-------------|----------|
| OAuth flows | 15+ | Mock provider APIs, test token lifecycle |
| Email integration | 20+ | Mock Gmail/Outlook APIs, test caching |
| Calendar integration | 15+ | Mock Google/Outlook APIs, test events |
| Task management | 25+ | CRUD, views, reminders, subtasks |
| Notes system | 20+ | CRUD, search, wiki-links, frontmatter |
| Document management | 25+ | Import, parse, chunk, index per format |
| Contacts | 15+ | CRUD, resolution, enrichment |
| OpenAI-compatible API | 25+ | Endpoints, auth, rate limiting, streaming |
| Workspace dashboard | 10+ | Aggregation, cross-tool linking |
| **Total V5** | **170+** | |

## Performance Targets

- OAuth callback: < 2s
- Email sync (100 messages): < 30s
- Calendar sync (50 events): < 10s
- Task creation: < 100ms
- Note search: < 200ms
- Document import (100 pages): < 30s
- Document search: < 500ms
- OpenAI API response: < 2s (first token < 500ms streaming)
- Workspace dashboard: < 1s
