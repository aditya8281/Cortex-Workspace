# V5 Phase 1: Email + Calendar Integration

**Duration estimate:** 10-14 days
**Dependencies:** V4 complete (scheduler, sessions, research)
**Risk:** HIGH — external API integrations, OAuth complexity, privacy concerns

---

## Goals

Integrate daily productivity tools: email and calendar. Connect to Gmail/Outlook via OAuth. Allow agent to read emails, check calendar, compose replies. Maintain local-first principle — data cached locally, never sent to third parties.

## Deliverables

1. Email integration (Gmail, Outlook via OAuth)
2. Calendar integration (Google Calendar, Outlook Calendar)
3. Email reading + search in agent
4. Calendar reading + event creation
5. Agent tools: read_email, search_email, compose_email, check_calendar, create_event
6. Email digest generation (daily/weekly summary)
7. Calendar-aware scheduling (check availability)
8. Local email cache (offline access)
9. OAuth flow (in-app browser for authentication)

## Architectural Changes

```
BEFORE:
  Cortex = internal tools only (memory, graph, search, vault, research)
  External = MCP tools (user-configured)

AFTER:
  Cortex = internal tools + daily productivity tools
  External integrations = Email (Gmail/Outlook) + Calendar (Google/Outlook)
  Data flow = OAuth → local cache → agent tools → user interaction
  Privacy = all data cached locally, no external storage
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/integrations/__init__.py` | Integrations package |
| `backend/app/services/integrations/oauth.py` | OAuth 2.0 flow manager |
| `backend/app/services/integrations/email/__init__.py` | Email package |
| `backend/app/services/integrations/email/base.py` | `Protocol[EmailProvider]` |
| `backend/app/services/integrations/email/gmail.py` | Gmail API integration |
| `backend/app/services/integrations/email/outlook.py` | Outlook API integration |
| `backend/app/services/integrations/email/cache.py` | Local email cache |
| `backend/app/services/integrations/email/digest.py` | Email digest generator |
| `backend/app/services/integrations/calendar/__init__.py` | Calendar package |
| `backend/app/services/integrations/calendar/base.py` | `Protocol[CalendarProvider]` |
| `backend/app/services/integrations/calendar/google.py` | Google Calendar API |
| `backend/app/services/integrations/calendar/outlook.py` | Outlook Calendar API |
| `backend/app/services/integrations/calendar/cache.py` | Local calendar cache |
| `backend/app/models/integration.py` | Integration credential storage |
| `backend/app/api/v1/integrations.py` | Integration management API |
| `migrations/versions/d00000000009_integrations.py` | Integration tables migration |

### OAuth Flow

```python
class OAuthManager:
    """Handle OAuth 2.0 flows for external providers."""

    PROVIDERS = {
        "gmail": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly",
                       "https://www.googleapis.com/auth/gmail.send",
                       "https://www.googleapis.com/auth/calendar"],
        },
        "outlook": {
            "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "scopes": ["Mail.Read", "Mail.Send", "Calendars.ReadWrite"],
        },
    }

    async def start_flow(self, provider: str, user_id: int) -> str:
        """Generate auth URL, store state, return URL for in-app browser."""
        state = secrets.token_urlsafe(32)
        await self._store_state(state, user_id, provider)
        return self._build_auth_url(provider, state)

    async def handle_callback(self, provider: str, code: str, state: str) -> Integration:
        """Exchange code for tokens, store encrypted."""
        tokens = await self._exchange_code(provider, code)
        return await self._store_tokens(provider, state, tokens)
```

### Email Provider Protocol

```python
class EmailProvider(Protocol):
    async def list_messages(
        self, query: str = "", max_results: int = 50
    ) -> list[EmailMessage]: ...

    async def get_message(self, message_id: str) -> EmailMessage: ...

    async def search_messages(self, query: str) -> list[EmailMessage]: ...

    async def send_message(self, to: str, subject: str, body: str) -> str: ...

    async def get_unread_count(self) -> int: ...
```

### Calendar Provider Protocol

```python
class CalendarProvider(Protocol):
    async def list_events(
        self, start: datetime, end: datetime
    ) -> list[CalendarEvent]: ...

    async def create_event(
        self, title: str, start: datetime, end: datetime,
        description: str = "", attendees: list[str] | None = None
    ) -> CalendarEvent: ...

    async def get_availability(self, date: datetime) -> list[TimeSlot]: ...

    async def list_calendars(self) -> list[Calendar]: ...
```

### Email Digest

```python
class EmailDigestGenerator:
    """Generate daily/weekly email summaries."""

    async def generate_daily(self, user_id: int) -> EmailDigest:
        emails = await self.email_provider.list_messages(
            query="newer_than:1d",
            max_results=100
        )
        # Categorize: urgent, important, newsletters, notifications
        categorized = await self._categorize(emails)
        # Summarize each category
        summary = await self._summarize(categorized)
        return EmailDigest(
            date=date.today(),
            total=len(emails),
            urgent=categorized.urgent,
            important=categorized.important,
            summary=summary,
        )
```

### Agent Tools

```python
@tool("read_email", "Read email messages", requires_approval=True)
async def read_email_tool(
    query: str = "",
    max_results: int = 10,
) -> str:
    """Read email messages matching query."""
    ...

@tool("search_email", "Search email messages")
async def search_email_tool(
    query: str,
    max_results: int = 20,
) -> str:
    """Search email messages."""
    ...

@tool("compose_email", "Compose and send email", requires_approval=True)
async def compose_email_tool(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
) -> str:
    """Compose and send an email."""
    ...

@tool("check_calendar", "Check calendar events")
async def check_calendar_tool(
    date: str = "today",
    days: int = 1,
) -> str:
    """Check calendar events for a date range."""
    ...

@tool("create_event", "Create calendar event", requires_approval=True)
async def create_event_tool(
    title: str,
    start: str,
    end: str,
    description: str = "",
    attendees: str = "",
) -> str:
    """Create a calendar event."""
    ...
```

### Migration

`d00000000009_integrations.py` creates:
- integrations table (id, user_id, provider, provider_user_id, access_token_encrypted, refresh_token_encrypted, expires_at, scopes, metadata, created_at, updated_at)
- email_cache table (id, user_id, message_id, subject, sender, snippet, body_encrypted, date, labels, fetched_at)
- calendar_cache table (id, user_id, event_id, calendar_id, title, start_time, end_time, description, attendees_json, fetched_at)

## Frontend Changes

| Page | Change |
|------|--------|
| Settings | New "Integrations" section |
| Settings → Integrations | Connect Gmail, Connect Outlook buttons |
| Dashboard | Email summary card (unread count, urgent count) |
| Dashboard | Today's calendar events card |
| Agent | Email/calendar tools in tool list |
| New: /email | Email browser (inbox view) |
| New: /calendar | Calendar view (day/week/month) |

### Settings → Integrations

```
┌─────────────────────────────────────────────────┐
│ Integrations                                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ 📧 Email                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ Gmail          🟢 Connected (adi@gmail.com) │ │
│ │ [Disconnect] [Sync Now] [Settings]          │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ Outlook        ⚪ Not connected              │ │
│ │ [Connect Outlook]                            │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ 📅 Calendar                                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ Google Cal     🟢 Connected                  │ │
│ │ Calendars: Personal, Work                    │ │
│ │ [Disconnect] [Sync Now] [Settings]          │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ Outlook Cal    ⚪ Not connected              │ │
│ │ [Connect Outlook Calendar]                   │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ⚙️  Sync Settings                               │
│ Email sync: [Every 15 min ▼]                    │
│ Calendar sync: [Every 5 min ▼]                  │
│ Local cache: [Enabled ✓]                        │
│ Offline access: [Enabled ✓]                     │
└─────────────────────────────────────────────────┘
```

## Memory Changes

Email content can be stored as memories. Key facts from emails extracted and stored with source attribution ("from email from X on Y date").

Calendar events stored as memories with temporal context.

## Retrieval Changes

Email and calendar content indexed into vector store. Search includes email/calendar results alongside other content.

## Agent Changes

Agent gains 5 new tools (read_email, search_email, compose_email, check_calendar, create_event). Tools with send/create actions require approval.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OAuth token expiry | High | Medium | Auto-refresh. Re-auth flow if refresh fails. |
| Email privacy | High | High | Local cache only. No external storage. Clear data policy. |
| API rate limits | High | Medium | Respect rate limits. Cache aggressively. Batch requests. |
| Calendar sync conflicts | Medium | Medium | Last-write-wins. Show conflicts to user. |
| OAuth complexity | Medium | Medium | Use established libraries (authlib, msal). |
| Email volume overwhelming | Medium | Medium | Digest system. Smart filtering. Priority scoring. |

## Exit Criteria

- [ ] Gmail OAuth flow works (connect, read, search, send)
- [ ] Outlook OAuth flow works (connect, read, search, send)
- [ ] Google Calendar OAuth works (list events, create events)
- [ ] Outlook Calendar OAuth works (list events, create events)
- [ ] Local email cache works (offline access)
- [ ] Local calendar cache works
- [ ] Email digest generation works
- [ ] Agent can read/search/send emails
- [ ] Agent can check/create calendar events
- [ ] All V1-V4 tests pass
- [ ] New integration tests
- [ ] `make lint` + `make format` clean
