# V5 Phase 3: Contacts + OpenAI-Compatible API

**Duration estimate:** 7-10 days
**Dependencies:** V5 Phase 1 (email, calendar), V5 Phase 2 (tasks, notes, documents)
**Risk:** Medium — OpenAI API compatibility surface area, contact privacy

---

## Goals

Build contacts system (people, relationships, communication history). Expose OpenAI-compatible API endpoint (so other tools can use Cortex as an LLM backend). Unify all daily tools into a cohesive workspace experience.

## Deliverables

1. Contacts system (people, organizations, relationships)
2. Contact-enriched email/calendar (auto-link contacts to communications)
3. OpenAI-compatible API endpoint (`/v1/chat/completions`)
4. API key management (generate, revoke, rate limit)
5. API usage tracking
6. Workspace dashboard (unified view of all daily tools)
7. Cross-tool workflows (email → task → note → document)

## Architectural Changes

```
BEFORE:
  Email, Calendar, Tasks, Notes, Documents = separate tools
  External API access = MCP only

AFTER:
  All daily tools = unified workspace with cross-references
  External API access = MCP + OpenAI-compatible API
  Contacts = entity linking across all tools
  API = /v1/chat/completions (OpenAI format)
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/contacts/__init__.py` | Contacts package |
| `backend/app/services/contacts/manager.py` | Contact CRUD + lifecycle |
| `backend/app/services/contacts/resolver.py` | Entity resolution (auto-link) |
| `backend/app/services/contacts/enricher.py` | Contact enrichment from email/calendar |
| `backend/app/services/api_compat/__init__.py` | OpenAI-compatible API package |
| `backend/app/services/api_compat/chat.py` | `/v1/chat/completions` endpoint |
| `backend/app/services/api_compat/models.py` | `/v1/models` endpoint |
| `backend/app/services/api_compat/middleware.py` | API key auth + rate limiting |
| `backend/app/services/api_compat/usage.py` | Usage tracking |
| `backend/app/services/workspace/__init__.py` | Workspace unification package |
| `backend/app/services/workspace/dashboard.py` | Unified workspace dashboard |
| `backend/app/services/workspace/crossref.py` | Cross-tool linking |
| `backend/app/models/contact.py` | Contact + ContactLink models |
| `backend/app/models/api_key.py` | APIKey + APIUsage models |
| `backend/app/api/v1/contacts.py` | Contacts API |
| `backend/app/api/v1/openai_compat.py` | OpenAI-compatible API routes |
| `backend/app/api/v1/workspace.py` | Workspace API |
| `migrations/versions/d00000000011_contacts_api.py` | Contacts + API tables |

### Contacts System

```python
class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    title = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class ContactLink(Base):
    """Links contacts to entities across the system."""
    __tablename__ = "contact_links"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    entity_type = Column(String, nullable=False)  # email, calendar_event, task, note, document
    entity_id = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)

class ContactManager:
    async def create(self, user_id: int, **kwargs) -> Contact: ...
    async def search(self, user_id: int, query: str) -> list[Contact]: ...
    async def get_communications(self, contact_id: int) -> list[Communication]: ...
    async def get_context(self, contact_id: int) -> ContactContext: ...

class ContactResolver:
    """Auto-link contacts to emails, calendar events, etc."""
    async def resolve_email_sender(self, sender: str, user_id: int) -> Contact | None: ...
    async def resolve_attendee(self, email: str, user_id: int) -> Contact | None: ...
    async def enrich_from_email(self, contact_id: int) -> None: ...
```

### OpenAI-Compatible API

```python
# /v1/chat/completions
class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: Usage

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    api_key: APIKey = Depends(verify_api_key),
) -> ChatCompletionResponse:
    """OpenAI-compatible chat completions endpoint."""
    # Route to Cortex agent loop
    response = await agent_loop(
        message=request.messages[-1].content,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=request.stream,
    )
    return ChatCompletionResponse(...)
```

### API Key Management

```python
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)  # SHA-256 of key
    key_prefix = Column(String, nullable=False)  # First 8 chars for display
    scopes = Column(JSON, default=list)  # ["chat", "memory", "search"]
    rate_limit = Column(Integer, default=100)  # requests per minute
    enabled = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
```

### Workspace Dashboard

Unified view combining all daily tools:

```python
class WorkspaceDashboard:
    async def get_summary(self, user_id: int) -> WorkspaceSummary:
        return WorkspaceSummary(
            email=await self._email_summary(user_id),      # unread, urgent
            calendar=await self._calendar_summary(user_id),  # today's events
            tasks=await self._task_summary(user_id),         # today, overdue, total
            notes=await self._notes_summary(user_id),        # recent, total
            documents=await self._docs_summary(user_id),     # recent, total
            contacts=await self._contacts_summary(user_id),  # recent, total
            agent=await self._agent_summary(user_id),        # recent runs, active
        )
```

### Migration

`d00000000011_contacts_api.py` creates:
- contacts table
- contact_links table
- api_keys table
- api_usage table (id, api_key_id, endpoint, tokens_used, latency_ms, created_at)

## Frontend Changes

| Page | Change |
|------|--------|
| Dashboard | Complete workspace dashboard (all tools unified) |
| New: /contacts | Contacts manager |
| New: /api-keys | API key management |
| Settings | API configuration section |
| All pages | Contact avatars + links where relevant |

### /contacts — Contact Manager

```
┌─────────────────────────────────────────────────┐
│ Contacts                                         │
├─────────────────────────────────────────────────┤
│ 🔍 Search contacts...                           │
│                                                 │
│ 👤 Alice Chen          eng lead @ Acme          │
│    alice@acme.com | 12 emails | 8 meetings     │
│    Last: 2d ago — "Re: API review"              │
│                                                 │
│ 👤 Bob Smith           PM @ Acme                │
│    bob@acme.com | 5 emails | 3 meetings        │
│    Last: 1d ago — "Sprint planning"             │
│                                                 │
│ [+ Add Contact] [🔗 Import from Email]          │
└─────────────────────────────────────────────────┘
```

### /api-keys — API Key Management

```
┌─────────────────────────────────────────────────┐
│ API Keys                                         │
├─────────────────────────────────────────────────┤
│                                                 │
│ 🔑 Production Key         Created: 7d ago       │
│    Prefix: sk-cortex-abc...                     │
│    Scopes: chat, memory, search                 │
│    Rate: 100 req/min | Used: 1,234 requests     │
│    Last used: 2h ago                            │
│    [View] [Revoke]                              │
│                                                 │
│ 🔑 Development Key        Created: 30d ago      │
│    Prefix: sk-cortex-def...                     │
│    Scopes: all                                  │
│    Rate: 50 req/min | Used: 456 requests        │
│    Last used: 1d ago                            │
│    [View] [Revoke]                              │
│                                                 │
│ [+ Generate New Key]                            │
│                                                 │
│ ─────────────────────────────────────────────── │
│ Usage (last 7 days)                             │
│ ████████████████████░░░░  3,456 requests        │
│ Avg latency: 245ms | Total tokens: 1.2M         │
└─────────────────────────────────────────────────┘
```

### Dashboard — Workspace View

```
┌──────────────────────────────────────────────────────┐
│ CORTEX Workspace                    Tuesday, Jun 25  │
├──────────────────────────────────────────────────────┤
│                                                      │
│ 📧 Email (3 unread, 1 urgent)     📅 Today (4 events)│
│ ┌────────────────────────┐ ┌────────────────────────┐│
│ │ 🔴 Urgent: client bug  │ │ 10:00 Standup          ││
│ │ 📩 PR review request   │ │ 14:00 Design review    ││
│ │ 📩 Newsletter digest   │ │ 16:00 1:1 with manager ││
│ └────────────────────────┘ │ 17:00 Team sync        ││
│                            └────────────────────────┘│
│                                                      │
│ ✅ Tasks (2 today, 1 overdue)    📝 Notes (recent)   │
│ ┌────────────────────────┐ ┌────────────────────────┐│
│ │ 🔴 Fix auth bug        │ │ Memory Architecture    ││
│ │ 🟡 Review PR #42       │ │ Sprint Planning Notes  ││
│ │ 🟢 Write V5 docs       │ │ API Design Ideas       ││
│ └────────────────────────┘ └────────────────────────┘│
│                                                      │
│ 🤖 Agent                    📄 Documents (recent)    │
│ ┌────────────────────────┐ ┌────────────────────────┐│
│ │ Last: 2h ago — success │ │ architecture-spec.pdf  ││
│ │ Running: none           │ │ meeting-notes.docx     ││
│ │ Sessions: 3 active     │ │ api-reference.md       ││
│ └────────────────────────┘ └────────────────────────┘│
└──────────────────────────────────────────────────────┘
```

## Memory Changes

Contact relationships stored as graph edges. Communication history enriches contact context. Cross-tool events (task from email, note from research) linked via contact graph.

## Retrieval Changes

Contacts added as context provider. Agent gains contact-aware retrieval ("what did Alice say about X?").

## Agent Changes

Agent gains contact-awareness. Can reference contacts in responses. Can create tasks from emails, notes from conversations, documents from research.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OpenAI API compatibility gaps | Medium | High | Test against popular clients. Document differences. |
| Contact privacy | High | High | Local-only. Clear data policy. User controls what's stored. |
| API key security | Medium | High | Hashed storage. Rate limiting. Usage monitoring. |
| Cross-tool complexity | Medium | Medium | Start simple (manual linking), add auto-linking later. |

## Exit Criteria

- [ ] Contact CRUD works
- [ ] Contact auto-linking works (email → contact)
- [ ] OpenAI-compatible /v1/chat/completions works
- [ ] OpenAI-compatible /v1/models works
- [ ] API key generation + revocation works
- [ ] API rate limiting works
- [ ] API usage tracking works
- [ ] Workspace dashboard shows unified view
- [ ] All V1-V5 Phase 1-2 tests pass
- [ ] New contacts + API + workspace tests
- [ ] `make lint` + `make format` clean
