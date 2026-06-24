# V4 Backend: The Automaton

## Overview

V4 makes Cortex self-maintaining and externally connectable. Task scheduler automates housekeeping. MCP server exposes Cortex tools to external clients. Session management enables persistent conversations. Deep research engine automates multi-step web research.

## File Structure (V4 additions)

```
backend/app/
├── services/
│   ├── scheduler/             # NEW: Task scheduler
│   │   ├── __init__.py
│   │   ├── engine.py          # Cron + event + webhook triggers
│   │   ├── triggers.py        # Trigger type definitions
│   │   ├── task_registry.py   # Task registration + metadata
│   │   └── history.py         # Task run history
│   ├── housekeeping/          # NEW: Automated maintenance
│   │   ├── __init__.py
│   │   ├── memory_decay.py
│   │   ├── embedding_refresh.py
│   │   ├── graph_cleanup.py
│   │   ├── staleness.py
│   │   ├── index_compaction.py
│   │   ├── log_rotation.py
│   │   └── health_check.py
│   ├── mcp/server/            # NEW: MCP server (expose tools)
│   │   ├── __init__.py
│   │   ├── server.py          # MCP server implementation
│   │   ├── handler.py         # Tool call handler
│   │   └── capabilities.py    # Server capabilities
│   ├── webhooks/              # NEW: Inbound webhooks
│   │   ├── __init__.py
│   │   ├── manager.py         # Webhook lifecycle
│   │   ├── dispatcher.py      # Inbound dispatch
│   │   └── models.py          # Webhook config models
│   ├── sessions/              # NEW: Session management
│   │   ├── __init__.py
│   │   ├── manager.py         # Session lifecycle
│   │   ├── state.py           # Conversation state persistence
│   │   └── context.py         # Session context
│   └── research/              # NEW: Deep research engine
│       ├── __init__.py
│       ├── engine.py          # Research orchestrator
│       ├── decomposer.py      # Question decomposition
│       ├── collector.py       # Web search + extraction
│       ├── synthesizer.py     # Multi-source synthesis
│       ├── gap_detector.py    # Follow-up generation
│       ├── reporter.py        # HTML + Markdown reports
│       └── budget.py          # Budget management
├── models/
│   ├── scheduled_task.py      # NEW
│   ├── task_history.py        # NEW
│   ├── session.py             # NEW
│   ├── webhook.py             # NEW
│   └── research.py            # NEW
├── api/v1/
│   ├── scheduler.py           # NEW: Scheduler management API
│   ├── sessions.py            # NEW: Session management API
│   ├── webhooks.py            # NEW: Webhook management API
│   ├── mcp_server.py          # NEW: MCP server management API
│   └── research.py            # NEW: Research API
└── migrations/
    └── versions/
        ├── d00000000006_scheduler.py    # Scheduler tables
        ├── d00000000007_sessions_webhooks.py  # Sessions + webhooks
        └── d00000000008_research.py     # Research tables
```

## Phase 1: Scheduler + Housekeeping

### 7 Housekeeping Tasks

| Task | Schedule | What It Does | Cost |
|------|----------|--------------|------|
| Memory Decay | Daily 2am | Reduce confidence of unused memories (×0.9 per 30 days) | Low |
| Embedding Refresh | Weekly Sun 3am | Re-embed content with updated models | Medium |
| Graph Cleanup | Daily 3am | Remove orphan nodes/edges | Low |
| Staleness Detection | Daily 4am | Flag memories not accessed in 90+ days | Low |
| Index Compaction | Weekly Sun 4am | Merge fragmented vector indices | Medium |
| Log Rotation | Daily 1am | Archive logs older than 30 days | Low |
| Health Check | Every 15min | Verify all services healthy | Low |

### Scheduler Engine

Cron expressions parsed with `croniter`. Event triggers subscribe to EventBus. Webhook triggers expose HTTP endpoints.

### Database Schema

scheduled_tasks: id, name, task_type (cron/event/webhook), schedule, handler, enabled, last_run, next_run, metadata
task_history: id, task_id, task_type, status, started_at, completed_at, duration_ms, error, metadata

## Phase 2: MCP Server + Sessions + Webhooks

### MCP Server

Exposes Cortex tools via MCP protocol. External clients (Claude Desktop, custom apps) can:
- List available Cortex tools
- Call Cortex tools with arguments
- Receive tool results

Two transports: stdio (local) and SSE (remote).

### Session Management

Persistent conversations with accumulated context:
- Create session → get session ID
- Send messages within session → context accumulates
- Resume session → full history + context restored
- Archive session → move to cold storage

### Webhook System

Inbound HTTP triggers:
- Generate unique URL per webhook
- HMAC signature verification
- Rate limiting per webhook
- Event filtering (only relevant events forwarded)
- Retry on failure (exponential backoff)

## Phase 3: Deep Research Engine

### Research Pipeline

1. **Decompose** (LLM): question → 3-7 sub-queries
2. **Collect**: web search + content extraction per sub-query
3. **Synthesize** (LLM): multi-source findings → structured analysis
4. **Gap detect** (LLM): identify missing information → follow-up queries
5. **Iterate**: repeat 2-4 until comprehensive or budget exhausted
6. **Report**: generate HTML + Markdown with executive summary, findings, sources

### Budget System

Configurable limits:
- Max queries: 20 (default)
- Max tokens: 100,000 (default)
- Max time: 5 minutes (default)
- Max sources: 50 (default)

## Testing Strategy

| Test Category | Count Target | Approach |
|--------------|-------------|----------|
| Scheduler | 20+ | Cron parsing, event triggers, webhook triggers |
| Housekeeping | 25+ | Each task individually, decay formulas, cleanup logic |
| MCP server | 20+ | Tool exposure, client connection, error handling |
| Sessions | 20+ | Create, resume, archive, context accumulation |
| Webhooks | 20+ | Inbound dispatch, signature verification, retry |
| Research | 25+ | Decomposition, collection, synthesis, reporting |
| Integration | 30+ | Cross-system: scheduler→housekeeping, session→agent |
| **Total V4** | **160+** | |

## Performance Targets

- Scheduler tick: < 100ms (check all cron tasks)
- Housekeeping task: < 60s per task (memory decay for 10K memories)
- MCP server tool call: < 100ms overhead (excluding tool execution)
- Webhook dispatch: < 50ms to reach handler
- Session resume: < 500ms (load context + recent messages)
- Research (20 queries): < 5 minutes
