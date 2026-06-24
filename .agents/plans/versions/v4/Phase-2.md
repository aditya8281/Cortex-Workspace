# V4 Phase 2: MCP Server + Webhooks + Sessions

**Duration estimate:** 7-10 days
**Dependencies:** V4 Phase 1 (scheduler), V2 Phase 2 (MCP client)
**Risk:** Medium — exposing Cortex as MCP server, session management complexity

---

## Goals

Expose Cortex as an MCP server (so external clients can use Cortex tools). Build webhook system for inbound integrations. Add session management (persistent conversations with state). Build the bridge between Cortex-as-server and Cortex-as-client.

## Deliverables

1. MCP server (expose Cortex tools to external clients)
2. Webhook system (inbound HTTP triggers)
3. Session management (persistent conversations with context)
4. Session API (create, resume, list, archive)
5. Conversation state persistence
6. MCP server configuration UI
7. Webhook management UI

## Architectural Changes

```
BEFORE:
  Cortex = MCP client (consumes external tools)
  Conversations = per-request, no persistent state

AFTER:
  Cortex = MCP client + MCP server (both consumes and exposes tools)
  Sessions = persistent conversations with state, context, history
  Webhooks = inbound HTTP triggers for external integrations
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/mcp/server/__init__.py` | MCP server package |
| `backend/app/services/mcp/server/server.py` | MCP server implementation |
| `backend/app/services/mcp/server/handler.py` | Tool call handler |
| `backend/app/services/mcp/server/capabilities.py` | Server capabilities declaration |
| `backend/app/services/webhooks/__init__.py` | Webhook package |
| `backend/app/services/webhooks/manager.py` | Webhook lifecycle management |
| `backend/app/services/webhooks/dispatcher.py` | Inbound webhook dispatch |
| `backend/app/services/webhooks/models.py` | Webhook configuration models |
| `backend/app/services/sessions/__init__.py` | Session package |
| `backend/app/services/sessions/manager.py` | Session lifecycle management |
| `backend/app/services/sessions/state.py` | Conversation state persistence |
| `backend/app/services/sessions/context.py` | Session context (what agent knows) |
| `backend/app/models/session.py` | Session SQLAlchemy model |
| `backend/app/models/webhook.py` | WebhookConfig SQLAlchemy model |
| `backend/app/api/v1/sessions.py` | Session management API |
| `backend/app/api/v1/webhooks.py` | Webhook management API |
| `backend/app/api/v1/mcp_server.py` | MCP server management API |
| `migrations/versions/d00000000007_sessions_webhooks.py` | Sessions + webhooks migration |

### MCP Server

Expose Cortex tools as MCP endpoints:
```python
class CortexMCPServer:
    """Expose Cortex tools to external MCP clients."""

    def __init__(self, tool_registry: ToolRegistry):
        self.tools = tool_registry
        self.server = Server("cortex", version="1.0.0")

    async def handle_list_tools(self) -> list[Tool]:
        """Return list of available Cortex tools."""
        return [
            Tool(name=t.name, description=t.description, inputSchema=t.schema)
            for t in self.tools.list_tools()
        ]

    async def handle_call_tool(self, name: str, arguments: dict) -> str:
        """Execute a Cortex tool."""
        return await self.tools.execute(name, arguments)
```

Transport options:
- **Stdio**: for local MCP clients (Claude Desktop, etc.)
- **SSE**: for remote MCP clients (web apps, services)

### Session Management

```python
class Session:
    id: str
    user_id: int
    title: str
    status: str  # active, paused, archived
    context: dict  # accumulated context (facts, decisions, state)
    messages: list[Message]
    metadata: dict  # tags, model used, token count
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None

class SessionManager:
    async def create(self, user_id: int, title: str) -> Session: ...
    async def resume(self, session_id: str) -> Session: ...
    async def archive(self, session_id: str) -> None: ...
    async def list(self, user_id: int, status: str = "active") -> list[Session]: ...
    async def get_context(self, session_id: str) -> ConversationContext: ...
```

### Webhook System

```python
class WebhookConfig:
    id: str
    name: str
    path: str  # unique URL path
    secret: str  # HMAC secret for verification
    enabled: bool
    events: list[str]  # which events to forward
    target: str  # internal handler or external URL
    metadata: dict

class WebhookDispatcher:
    async def receive(self, path: str, payload: dict, headers: dict) -> Response:
        """Verify signature, dispatch to handler."""
        webhook = await self._get_webhook(path)
        if not webhook.enabled:
            return Response(status=404)

        if not self._verify_signature(webhook.secret, payload, headers):
            return Response(status=401)

        await self._dispatch(webhook, payload)
        return Response(status=200)
```

## Frontend Changes

| Page | Change |
|------|--------|
| Settings | New "MCP Server" section (expose Cortex as server) |
| Settings | New "Webhooks" section (list, add, remove, test) |
| Settings | New "Sessions" section (list, archive, settings) |
| Conversations | Session-aware (resume previous sessions) |
| Header | Session selector dropdown |

### Session UI

Conversations page gains session management:
- Session list (active, archived)
- Resume session (loads context + history)
- Archive session
- Session metadata (model, tokens, duration)

### Webhook Settings

```
┌─────────────────────────────────────────────────┐
│ Webhooks                                        │
├─────────────────────────────────────────────────┤
│                                                 │
│ 📡 GitHub Push     /webhooks/github    [ON] ▶│
│    Last: 5m ago    Events: push, PR     ✅     │
│                                                 │
│ 📡 Slack Events    /webhooks/slack     [ON] ▶│
│    Last: 1h ago    Events: message      ✅     │
│                                                 │
│ [+ Add Webhook]                                 │
│                                                 │
│ ─────────────────────────────────────────────── │
│ Cortex MCP Server                               │
│ Transport: [Stdio ▼] [SSE ▼]                    │
│ Status: 🟢 Running on :3001                     │
│ Available tools: 15                             │
│ [Copy Connection Config]                        │
└─────────────────────────────────────────────────┘
```

## Memory Changes

No changes.

## Retrieval Changes

No changes.

## Agent Changes

Agent now operates within sessions. Session context accumulates across conversations within a session. Agent can access session state for continuity.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MCP server security | Medium | High | Authentication required. Rate limiting. Tool whitelist. |
| Webhook security | Medium | High | HMAC signature verification. IP allowlisting. |
| Session state bloat | Medium | Medium | Auto-archive sessions > 30 days. Compress old context. |
| MCP server resource usage | Low | Medium | Connection limits. Timeout on idle connections. |

## Exit Criteria

- [ ] Cortex exposes tools as MCP server (stdio + SSE)
- [ ] External MCP client can call Cortex tools
- [ ] Webhook receives inbound HTTP requests
- [ ] Webhook verifies HMAC signatures
- [ ] Sessions persist across conversations
- [ ] Session resume loads full context
- [ ] Settings UI shows MCP server status
- [ ] Settings UI manages webhooks
- [ ] All V1-V4 Phase 1 tests pass
- [ ] New MCP server + webhook + session tests
- [ ] `make lint` + `make format` clean
