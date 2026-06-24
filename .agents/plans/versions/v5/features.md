# CORTEX V5: "The Workspace"

**Version:** 5
**Date:** 2026-06-25
**Status:** Planned

---

## 1. Goals

V5 transforms CORTEX from a code intelligence tool into a complete AI workspace. Email, calendar, tasks, notes, documents, and contacts — the full daily productivity layer from Odysseus, rebuilt on Cortex's superior infrastructure.

This is the version where CORTEX understands not just your code, but your life. It reads your email, manages your calendar, tracks your tasks, and organizes your notes — all with the same intelligence layer that understands your codebase.

### Primary Goals

1. **Email system** — IMAP/SMTP, thread parsing, triage, AI reply, writing style
2. **Calendar system** — CRUD, ICS import, CalDAV sync, RRULE recurrence, NL parsing
3. **Tasks system** — CRUD, cron/event/webhook triggers, housekeeping integration
4. **Notes system** — Checklists, pin/archive, reminders, LLM synthesis
5. **Documents system** — Living docs, version history, PDF export, AI tidy
6. **Contacts system** — CardDAV, vCard/CSV import, resolution
7. **OpenAI-compatible API** — Expose Cortex as OpenAI-compatible endpoint

### Non-Goals (Explicitly Deferred)

- Community plugin marketplace (V6)
- Workflow DAGs (V6)
- Cross-encoder reranking (V6, if GPU available)

---

## 2. Scope

### 2.1 Email System

| Feature | V5 Implementation | Source |
|---------|-------------------|--------|
| IMAP connection | Connect to any IMAP server | Odysseus email.py (3,694 lines) |
| SMTP sending | Send emails via SMTP | Odysseus |
| Thread parsing | Parse email threads, extract participants | Odysseus |
| Triage | Auto-categorize incoming email (urgent, FYI, newsletter, etc.) | Odysseus |
| AI reply | Generate draft replies based on context | Odysseus |
| Writing style | Learn user's writing style from sent mail | Odysseus |
| Search | Full-text search across all email | Custom (uses existing fulltext search) |
| Memory integration | Email facts extracted into memory | Custom (uses V2 memory pipeline) |

**Scope boundary:** Email is read-only in first pass. Sending is added after read works reliably. OAuth2 for Gmail/Outlook deferred (basic IMAP/SMTP first).

**Models:** `EmailAccount`, `EmailMessage`, `EmailTag`, `EmailThread`

### 2.2 Calendar System

| Feature | V5 Implementation | Source |
|---------|-------------------|--------|
| CRUD | Create, read, update, delete events | Odysseus calendar.py (1,545 lines) |
| ICS import | Import .ics calendar files | Odysseus |
| CalDAV sync | Sync with CalDAV servers (Radicale, Nextcloud) | Odysseus |
| RRULE | Recurring event support | Odysseus |
| NL parsing | "Meeting tomorrow at 3pm" → calendar event | Odysseus |
| Agent integration | Agent can create/check/schedule events | Custom |
| Conflict detection | Warn about scheduling conflicts | Custom |

**Scope boundary:** CalDAV sync is one-way (pull) in first pass. Two-way sync deferred. Google Calendar API deferred (CalDAV works for most servers).

**Models:** `Calendar`, `CalendarEvent`, `CalendarReminder`

### 2.3 Tasks System

| Feature | V5 Implementation | Source |
|---------|-------------------|--------|
| CRUD | Create, read, update, delete tasks | Odysseus tasks.py (1,166 lines) |
| Priority | High/medium/low priority levels | Odysseus |
| Due dates | Due date + overdue detection | Odysseus |
| Recurring | Recurring task templates | Odysseus |
| Triggers | Cron/event/webhook triggers (uses V4 scheduler) | Odysseus |
| Agent integration | Agent can create/complete/list tasks | Custom |
| Integration with housekeeping | Tasks created by housekeeping pipeline | Custom (V4) |

**Scope boundary:** Tasks are simple CRUD + triggers. No project management, no kanban boards, no Gantt charts. YAGNI.

**Models:** `Task`, `TaskTemplate`

### 2.4 Notes System

| Feature | V5 Implementation | Source |
|---------|-------------------|--------|
| CRUD | Create, read, update, delete notes | Odysseus notes.py (905 lines) |
| Checklists | Toggle-able checklist items | Odysseus |
| Pin/Archive | Pin important notes, archive completed | Odysseus |
| Reminders | Time-based reminders via scheduler | Odysseus |
| LLM synthesis | Agent can summarize, expand, or reformat notes | Custom |
| Memory integration | Note facts extracted into memory | Custom (V2 memory pipeline) |
| Search | Full-text search across notes | Custom |

**Scope boundary:** Notes are markdown-based. No rich text editor. No real-time collaboration. YAGNI.

**Models:** `Note`, `NoteReminder`

### 2.5 Documents System

| Feature | V5 Implementation | Source |
|---------|-------------------|--------|
| Living docs | Documents that evolve over time | Odysseus documents.py (1,726 lines) |
| Version history | Track changes, diff, revert | Odysseus |
| PDF export | Generate PDF from document | Odysseus |
| AI tidy | Agent can clean up, reformat, improve documents | Custom |
| Templates | Document templates for common formats | Odysseus |
|嵌入式 indexing | Documents indexed for search (uses existing indexer) | Custom |

**Scope boundary:** Documents are markdown-based with version history. No WYSIWYG editor. No real-time collaboration. PDF export via library, not rendering engine.

**Models:** `Document`, `DocumentVersion`, `DocumentTemplate`

### 2.6 Contacts System

| Feature | V5 Implementation | Source |
|---------|-------------------|--------|
| CRUD | Create, read, update, delete contacts | Odysseus contacts.py (893 lines) |
| CardDAV | Sync with CardDAV servers | Odysseus |
| vCard import | Import .vcf files | Odysseus |
| CSV import | Import CSV contact lists | Odysseus |
| Resolution | Deduplicate contacts across sources | Odysseus |
| Email integration | Link contacts to email threads | Custom |

**Scope boundary:** CardDAV sync is one-way (pull) in first pass. Contact resolution is basic (name + email matching). YAGNI.

**Models:** `Contact`, `ContactGroup`

### 2.7 OpenAI-Compatible API

| Endpoint | V5 Implementation | Source |
|----------|-------------------|--------|
| `/v1/chat/completions` | OpenAI-compatible chat endpoint | Open WebUI + AnythingLLM pattern |
| `/v1/models` | List available models | Custom |
| `/v1/embeddings` | OpenAI-compatible embedding endpoint | Custom |

**Scope boundary:** OpenAI-compatible API wraps Cortex's existing LLM, embedding, and agent capabilities. It does NOT replace the native API. It enables external tools that expect OpenAI format.

### 2.8 Vault Settings

| Feature | V5 Implementation | Source |
|---------|-------------------|--------|
| Per-vault config | Provider overrides per vault | AnythingLLM pattern (AD10) |
| Per-project settings | Different models/prompts per project | Custom |
| Settings UI | Settings page in desktop shell + web UI | Custom |

---

## 3. Success Criteria

### Functional

| Criterion | Measure |
|-----------|---------|
| Email | Connect to IMAP, read email, parse threads, triage, draft replies |
| Calendar | Create events, import ICS, parse "tomorrow at 3pm" |
| Tasks | CRUD + triggers via scheduler |
| Notes | CRUD + checklists + reminders |
| Documents | Living docs with version history + PDF export |
| Contacts | CRUD + vCard/CSV import + basic resolution |
| OpenAI API | External tool can call `/v1/chat/completions` and get Cortex response |
| Memory integration | Email, notes, contacts facts extracted into memory pipeline |
| Zero regression | V1 + V2 + V3 + V4 functionality preserved |

### Quality

| Criterion | Measure |
|-----------|---------|
| Email parsing | Handles common formats (Gmail, Outlook, Apple Mail) |
| Calendar parsing | Handles standard RRULE patterns |
| Contact resolution | >90% accuracy for duplicate detection |
| OpenAI API | Passes basic OpenAI API compatibility tests |
| Test count | V4 count + new daily productivity tests |
| Performance | Email sync < 30s for 1000 messages |

---

## 4. User Impact

### Before V5

- CORTEX understands code only
- No email integration
- No calendar management
- No task tracking
- No note organization
- No document management
- No contact management
- External tools can't use Cortex (no OpenAI-compatible API)

### After V5

- CORTEX understands code AND daily life
- Email: read, triage, draft replies, search
- Calendar: create events, NL parsing, conflict detection
- Tasks: CRUD + automated triggers
- Notes: checklists, reminders, LLM synthesis
- Documents: living docs with version history
- Contacts: organized, deduplicated, linked to email
- External tools: OpenAI-compatible API enables integration

### Who Benefits

| User | How |
|------|-----|
| Developers | Code intelligence + email/calendar/tasks in one tool |
| Researchers | Notes + documents + deep research engine |
| Power users | Full AI workspace, OpenAI-compatible API |
| Teams | MCP server (V4) + OpenAI API = multi-client access |

---

## 5. Architecture Impact

### What Changes

```
V4:
  Intelligence layer: Memory, Graph, Retrieval, Agent
  Daily tools: None

V5:
  Intelligence layer: Memory, Graph, Retrieval, Agent
  Daily tools: Email, Calendar, Tasks, Notes, Documents, Contacts
  External API: OpenAI-compatible endpoint
```

### New Components

| Component | Purpose |
|-----------|---------|
| Email service | IMAP/SMTP, thread parsing, triage, AI reply |
| Calendar service | CRUD, ICS, CalDAV, RRULE, NL parsing |
| Tasks service | CRUD, triggers, housekeeping integration |
| Notes service | CRUD, checklists, reminders, LLM synthesis |
| Documents service | Living docs, version history, PDF export |
| Contacts service | CRUD, CardDAV, vCard/CSV, resolution |
| OpenAI adapter | Wrap Cortex capabilities as OpenAI-compatible API |
| Vault settings | Per-vault provider overrides |
| New models (12) | EmailAccount, EmailMessage, EmailTag, EmailThread, Calendar, CalendarEvent, CalendarReminder, Task, TaskTemplate, Note, NoteReminder, Document, DocumentVersion, DocumentTemplate, Contact, ContactGroup |
| New migrations | 6+ migrations for daily productivity tables |

### What Stays

| Component | Why |
|-----------|-----|
| All V1 + V2 + V3 + V4 functionality | Complete daemon, agent, CLI, services, plugins, MCP, desktop, scheduler |
| Memory pipeline | Email, notes, contacts facts extracted into memory |
| Event bus | Daily tools publish events |
| Job queue | Background sync, indexing, extraction |

---

## 6. UX Impact

### Surfaces

| Surface | V5 Change |
|---------|-----------|
| Desktop shell | New: email viewer, calendar view, task list, notes editor, document viewer, contacts |
| CLI | New commands: `cortex email list/read/send`, `cortex calendar list/create`, `cortex task list/add/complete`, `cortex note list/create`, `cortex document list/create`, `cortex contact list/add` |
| API | New endpoints: email, calendar, tasks, notes, documents, contacts CRUD |
| Web UI | New pages: email, calendar, tasks, notes, documents, contacts |

### Interaction Model

| Before V5 | After V5 |
|-----------|----------|
| CORTEX only knows code | CORTEX knows code + email + calendar + tasks + notes + contacts |
| User manages email in separate app | Agent triages email, drafts replies |
| User manages calendar in separate app | Agent creates events from natural language |
| User tracks tasks in separate app | Agent manages tasks with automated triggers |
| External tools can't use Cortex | OpenAI-compatible API enables integration |

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Email IMAP complexity | High | High | Start with read-only. Add send in second pass. Handle OAuth2 carefully. |
| CalDAV compatibility | Medium | High | Test against Radicale, Nextcloud, Google Calendar. Handle RRULE edge cases. |
| Scope creep (daily tools) | High | High | Each tool gets own spec → plan → implement. Never more than 2 simultaneously. |
| Database migration complexity | Medium | Medium | 6+ new migrations. Test each individually. |
| Performance with large email/mailbox | Medium | Medium | Incremental sync. Index only recent messages first. |
| OpenAI API compatibility | Low | Medium | Use established library. Test against common OpenAI clients. |
| Contact resolution accuracy | Medium | Low | Start with basic name+email matching. Improve iteratively. |

---

## 8. Exit Criteria (V5 Complete When)

- [ ] Email: IMAP connect, read, parse threads, triage, draft replies
- [ ] Calendar: CRUD, ICS import, NL parsing, conflict detection
- [ ] Tasks: CRUD + triggers via scheduler
- [ ] Notes: CRUD + checklists + reminders + LLM synthesis
- [ ] Documents: Living docs + version history + PDF export
- [ ] Contacts: CRUD + vCard/CSV import + basic resolution
- [ ] OpenAI-compatible API: `/v1/chat/completions` works
- [ ] Memory integration: Email, notes, contacts facts extracted
- [ ] All daily productivity models created + migrations applied
- [ ] All V1 + V2 + V3 + V4 tests pass
- [ ] New daily productivity tests
- [ ] Email sync < 30s for 1000 messages
- [ ] Desktop shell shows daily productivity surfaces
