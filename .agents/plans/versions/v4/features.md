# CORTEX V4: "The Automaton"

**Version:** 4
**Date:** 2026-06-25
**Status:** Planned

---

## 1. Goals

V4 makes CORTEX autonomous. Task scheduling, housekeeping, webhooks, and the MCP server transform it from a tool you use into a system that works for you. CORTEX runs background tasks, maintains itself, and integrates with external automation platforms.

This is the version where CORTEX stops being reactive and starts being proactive. It maintains its own memory, indexes its own files, cleans up its own data, and responds to external triggers.

### Primary Goals

1. **Task scheduler** — Cron/event/webhook triggers for autonomous operation
2. **Housekeeping** — Automatic memory decay, embedding refresh, graph maintenance, staleness detection
3. **Webhooks** — CRUD + test for outgoing webhooks. API token sync with n8n/Make/Activepieces.
4. **MCP server** — Expose Cortex tools to other MCP clients
5. **Agent-to-agent sessions** — Named sessions with model selection, archive, fork, truncate
6. **Deep research engine** — Multi-step web research with HTML report generation

### Non-Goals (Explicitly Deferred)

- Daily productivity tools (V5)
- Community plugin marketplace (V5)
- Ecosystem features (V6)
- Workflow DAGs (V6)

---

## 2. Scope

### 2.1 Task Scheduler

| Trigger Type | V4 Implementation | Source |
|-------------|-------------------|--------|
| Cron | Schedule tasks at fixed intervals | Odysseus task_scheduler.py (2,467 lines) |
| Event | Trigger on system events (file_changed, memory_decayed, etc.) | Odysseus event triggers |
| Webhook | Trigger on incoming HTTP webhook | Odysseus webhook triggers |
| Manual | User-initiated via CLI or API | Custom |

| Built-in Housekeeping Tasks | What They Do |
|---------------------------|-------------|
| Memory decay | Run confidence decay on all memories |
| Embedding refresh | Re-embed memories with stale embeddings |
| Graph maintenance | Remove orphaned nodes, update stale edges |
| Staleness detection | Mark files that haven't been re-indexed |
| Index optimization | Compact index, remove deleted files |
| Cleanup | Remove expired data, old logs, orphaned records |

**Scope boundary:** The scheduler runs as part of the daemon. It uses the event bus for triggers and the job queue for execution. It does NOT require a separate process.

### 2.2 Housekeeping Pipeline

| Task | Frequency | What It Does |
|------|-----------|-------------|
| Memory decay | Daily | Apply confidence decay formula to all memories |
| Embedding refresh | Weekly | Re-embed memories older than 90 days |
| Graph cleanup | Daily | Remove nodes with no edges, update stale relationships |
| Staleness scan | On file change | Mark files that haven't been indexed |
| Index compaction | Weekly | Optimize Qdrant collections, remove deleted files |
| Log rotation | Daily | Rotate and compress old logs |
| Health self-check | Every 30min | Probe all dependencies, report status |

**Scope boundary:** Housekeeping tasks are background jobs. They do NOT block user interaction. They publish events when complete.

### 2.3 Webhooks

| Aspect | V4 Design | Source |
|--------|----------|--------|
| CRUD | Create, read, update, delete webhooks | Odysseus webhook_routes.py (395 lines) |
| Test | Send test payload to webhook URL | Odysseus test endpoint |
| API token sync | Sync tokens with n8n, Make, Activepieces | Odysseus pattern |
| Provider auto-detect | Detect webhook platform from URL/response | Odysseus pattern |
| Events | Webhooks fire on: job_complete, memory_decayed, index_complete, agent_complete | Custom |

**Scope boundary:** Webhooks are outgoing only (Cortex → external). Incoming webhooks are a trigger type for the scheduler.

### 2.4 MCP Server

| Aspect | V4 Design |
|--------|----------|
| Expose | Cortex tools (search, memory, graph, agent) to other MCP clients |
| Transport | Stdio (for local MCP clients) |
| Authentication | None (local-only, same machine) |
| Tool selection | User configures which tools are exposed |
| Versioning | MCP server versioned independently |

**Scope boundary:** MCP server is added after MCP client (V2) is stable. It exposes a curated subset of Cortex tools, not all internal services.

### 2.5 Agent-to-Agent Sessions

| Feature | V4 Implementation | Source |
|---------|-------------------|--------|
| Create session | Named session with model selection | Odysseus session_tools.py (465 lines) |
| Send message | Send message to session, get response | Odysseus |
| List sessions | List active and archived sessions | Odysseus |
| Archive | Archive completed sessions | Odysseus |
| Fork | Fork session from a specific point | Odysseus |
| Truncate | Remove history from a session | Odysseus |

**Scope boundary:** Sessions are agent-owned conversations with persistent state. They enable multi-step workflows where the agent maintains context across interactions.

### 2.6 Deep Research Engine

| Feature | V4 Implementation | Source |
|---------|-------------------|--------|
| Multi-step research | Iterative web search + synthesis | Odysseus research.py (1,165 lines) |
| Source tracking | Track all sources consulted | Odysseus |
| HTML report | Generate formatted research report | Odysseus |
| Citation management | Link claims to sources | Odysseus |
| Budget control | Limit research depth by token budget | Custom |

**Scope boundary:** Research is a background task. It uses web_fetch tool + LLM synthesis. It does NOT require any new infrastructure.

### 2.7 Additional V4 Capabilities

| Capability | Why |
|-----------|-----|
| Teacher escalation | LLM-to-LLM consultation for complex questions (Odysseus pattern) |
| RAG-based tool selection | When tool count > 15, use embedding-based tool retrieval (Odysseus pattern) |
| Domain-specific rules | Tool-to-domain mapping for context injection (Odysseus pattern) |
| Session search | Full-text search across conversation sessions (Odysseus pattern) |
| Runtime skill injection | Jaccard-matched skill injection based on user message (Odysseus pattern) |

---

## 3. Success Criteria

### Functional

| Criterion | Measure |
|-----------|---------|
| Task scheduler | Cron jobs execute at scheduled times. Event triggers fire on conditions. |
| Housekeeping | Memory decay runs daily. Graph cleanup runs daily. Index optimization runs weekly. |
| Webhooks | User can create webhook, test it, receive payloads on events |
| MCP server | External MCP client can connect and use Cortex tools |
| Agent sessions | User can create named session, send messages, archive |
| Research engine | Agent can conduct multi-step research, produce HTML report |
| Zero regression | V1 + V2 + V3 functionality preserved |

### Quality

| Criterion | Measure |
|-----------|---------|
| Scheduler reliability | 99%+ of scheduled tasks execute on time |
| Housekeeping | Memory count stays stable (decay balances new additions) |
| Webhook delivery | 99%+ delivery rate with retry |
| MCP server | External client can use 3+ Cortex tools |
| Test count | V3 count + new scheduler/webhook/MCP server/research tests |

---

## 4. User Impact

### Before V4

- CORTEX is reactive — it only works when you use it
- No automatic maintenance — memory accumulates, index gets stale
- No integration with automation platforms
- No multi-step research capability
- No agent-to-agent coordination

### After V4

- CORTEX maintains itself (memory decay, graph cleanup, index optimization)
- CORTEX responds to external triggers (webhooks, events)
- CORTEX integrates with n8n, Make, Activepieces via webhooks
- CORTEX conducts deep research autonomously
- CORTEX agents coordinate through named sessions

### Who Benefits

| User | How |
|------|-----|
| Automation users | Webhooks + scheduler enable CI/CD-style automation |
| Power users | Deep research engine, agent sessions, skill injection |
| Teams | MCP server enables multi-client access |
| All users | Housekeeping keeps the system healthy without manual intervention |

---

## 5. Architecture Impact

### What Changes

```
V3:
  User → daemon (manual interaction)
  Background jobs (indexing, embedding)

V4:
  User → daemon (manual interaction)
  Scheduler → daemon (autonomous triggers)
  Webhooks → daemon (external triggers)
  MCP clients → MCP server → daemon (external access)
  Housekeeping → daemon (self-maintenance)
  Research engine → daemon (autonomous research)
```

### New Components

| Component | Purpose |
|-----------|---------|
| Task scheduler | Cron/event/webhook trigger management |
| Housekeeping pipeline | Automatic maintenance tasks |
| Webhook service | Outgoing webhook management |
| MCP server | Expose Cortex tools to external MCP clients |
| Session manager | Agent-to-agent session persistence |
| Research engine | Multi-step web research + report generation |
| Skill injection | Runtime skill matching and injection |
| Tool selector | RAG-based tool selection when > 15 tools |

### What Stays

| Component | Why |
|-----------|-----|
| All V1 + V2 + V3 functionality | Daemon, agent, CLI, services, plugins, MCP client, desktop |
| Event bus | Scheduler and housekeeping use events |
| Job queue | Scheduler and housekeeping use jobs |
| Plugin system | MCP server is a plugin |

---

## 6. UX Impact

### Surfaces

| Surface | V4 Change |
|---------|-----------|
| Desktop shell | New: scheduler status, webhook management, research results |
| CLI | New commands: `cortex schedule list/run`, `cortex webhook create/test`, `cortex research "topic"` |
| API | New endpoints: scheduler CRUD, webhook CRUD, research trigger, MCP server management |
| Web UI | New: scheduler dashboard, webhook management, research viewer |

### Interaction Model

| Before V4 | After V4 |
|-----------|----------|
| User manually triggers indexing | Scheduler triggers indexing on file changes |
| Memory accumulates forever | Housekeeping decays old memories |
| No external integration | Webhooks fire on events, MCP server exposes tools |
| Agent works only when asked | Agent conducts research autonomously |
| Single agent per task | Multiple named sessions coordinate |

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Scheduler reliability | Medium | High | Persistent job queue (from V2). Retry logic. Dead-letter queue. |
| Housekeeping interference | Medium | Medium | Housekeeping runs during low-activity periods. Configurable schedule. |
| Webhook delivery failures | Medium | Medium | Retry with exponential backoff. Delivery status tracking. |
| MCP server security | Medium | High | Local-only (no network exposure). Tool selection is curated. |
| Research engine quality | Medium | Medium | Budget controls. Source tracking. Human review option. |
| Session complexity | Low | Medium | Simple CRUD. No complex orchestration. |

---

## 8. Exit Criteria (V4 Complete When)

- [ ] Task scheduler executes cron, event, and webhook triggers
- [ ] 7 housekeeping tasks run on schedule
- [ ] Webhooks: create, test, receive payloads on events
- [ ] MCP server exposes 3+ Cortex tools to external clients
- [ ] Agent-to-agent sessions: create, send, list, archive, fork
- [ ] Deep research engine: multi-step research, HTML report
- [ ] Teacher escalation: LLM-to-LLM consultation works
- [ ] RAG-based tool selection operational (when > 15 tools)
- [ ] Runtime skill injection operational
- [ ] All V1 + V2 + V3 tests pass
- [ ] New scheduler/webhook/MCP server/research tests
- [ ] Scheduler reliability > 99%
- [ ] Webhook delivery rate > 99%
