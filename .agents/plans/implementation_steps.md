# Implementation Steps

The definitive contributor guide. A new contributor should be able to start implementation using only: `guide.md` + `progress.md` + `implementation_steps.md` + `versions/` without requiring another strategic planning cycle.

---

## 1. Quick Start

### Prerequisites

- **Python 3.11+**, **Node.js 18+**, **Docker** (for dev infrastructure)
- **PostgreSQL, Redis, Qdrant** via Docker Compose
- **Claude Code** or compatible AI assistant

### First Steps

1. **Read `guide.md`** — the constitution. Understand what Cortex is and where it's going.
2. **Read `implementation_steps.md`** — this document. Understand the execution plan.
3. **Pick a version** (start at V1). Read `versions/v1/features.md` for context.
4. **Read the first phase:** `versions/v1/Phase-1.md`. This is your first task.
5. **Execute** following the phase's TDD instructions.

---

## 2. Execution Philosophy

### Principles

- **One phase at a time.** Phases are capability milestones, not calendar commitments.
- **TDD for every new subsystem.** Write failing test → implement → verify pass → commit.
- **Feature flags for risky changes.** Agent loop, vector store abstraction — all behind flags.
- **Small, focused commits.** Each commit is self-contained and testable.
- **`make lint` + `make format` after each commit.** No exceptions.
- **All 341+ existing tests must pass after every change.** Zero regression.

### Branch Strategy

- `feat/v1-phase-1-daemon` for V1 Phase-1
- `feat/v1-phase-2-agent` for V1 Phase-2
- `feat/v2-phase-1-abstraction` for V2 Phase-1
- Pattern: `feat/v{version}-phase-{n}-{topic}`
- Merge to `main` after each phase is verified.

---

## 3. Version Execution Order

---

### V1: The Brain Works (Foundation)

**Duration:** 11–18 days
**Prerequisites:** None
**Why first:** Everything else depends on V1.

#### V1 Phase-1: Daemon Foundation (3–5 days)

| Attribute | Value |
|-----------|-------|
| Risk | Low |
| Entry criteria | Current codebase compiles, tests pass |
| Exit criteria | `cortexd start/stop/status/logs` works. All 341+ tests pass. |

**Deliverables:**
- `cortexd` entrypoint
- PID management
- Health checks
- Graceful shutdown
- Sleep/wake lifecycle

**Key files:**
- `backend/app/daemon/` (7 new files)
- `backend/app/main.py` (modified)

---

#### V1 Phase-2: Agent Loop Rebuild (5–8 days)

| Attribute | Value |
|-----------|-------|
| Risk | **HIGH** — replaces central nervous system |
| Entry criteria | V1 Phase-1 complete (daemon running) |
| Exit criteria | Feature flag controls old vs new agent path. Both paths tested. All 341+ tests pass. |

**Deliverables:**
- Single streaming agent loop
- `@tool` decorator
- 15+ tools with schemas
- Compaction
- Prompt security
- Intent classification
- Stall detection
- Completion verifier

**Key files:**
- `backend/app/agents/loop.py`
- `backend/app/agents/tools/` package
- 12+ new files

> ⚠️ **Critical:** This is the single most impactful change. The agent loop is the central nervous system. Test against ALL existing tests before and after.

---

#### V1 Phase-3: CLI + Bug Fixes (3–5 days)

| Attribute | Value |
|-----------|-------|
| Risk | Low |
| Entry criteria | V1 Phase-1 complete (daemon running, CLI can connect) |
| Exit criteria | All 15 CLI commands return correct results. All 341+ tests pass. |

**Deliverables:**
- 15 working CLI commands
- 5 bug fixes
- Documentation cleanup

**Key files:**
- `cli/src/commands/` (15 files modified)
- Bug fix files

---

### V2: The Architecture (Extensibility)

**Duration:** 17–25 days
**Prerequisites:** V1 complete
**Why second:** Establishes service boundaries and extensibility before building features on top.

#### V2 Phase-1: Service Abstraction + Event Bus (5–8 days)

| Attribute | Value |
|-----------|-------|
| Risk | Medium — interface design requires foresight |
| Entry criteria | V1 complete |
| Exit criteria | New provider can be registered without modifying core code. Services communicate via events. |

**Deliverables:**
- 5 Protocol interfaces
- Provider registry
- In-process event bus
- Event tracing

**Key files:**
- `backend/app/core/providers/` (7 new)
- `backend/app/core/events/` (4 new)

---

#### V2 Phase-2: MCP Client + Plugins (5–7 days)

| Attribute | Value |
|-----------|-------|
| Risk | Medium — MCP ecosystem still evolving |
| Entry criteria | V2 Phase-1 complete (abstractions in place) |
| Exit criteria | External MCP tools appear as native Cortex tools. Plugin guide published. |

**Deliverables:**
- MCP client (stdio + SSE)
- MCPTool wrapper
- 3-layer plugin architecture
- Plugin authoring guide

**Key files:**
- `backend/app/services/mcp/` (7 new)
- `backend/app/plugins/` (4 new)

---

#### V2 Phase-3: Memory Consolidation + Context Providers (7–10 days)

| Attribute | Value |
|-----------|-------|
| Risk | **HIGH** — memory quality directly affects reliability |
| Entry criteria | V2 Phase-1 (event bus), V2 Phase-2 (MCP) |
| Exit criteria | Memory consolidates automatically. Context is composable. Config hierarchy works. |

**Deliverables:**
- Memory consolidation pipeline
- LLM extraction
- Bi-temporal tracking
- Context providers
- PersistentConfig
- Model routing

**Key files:**
- `backend/app/services/memory/` (6 new)
- `backend/app/services/context/` (8 new)
- 5 migrations

---

### V3: The Desktop (Native Experience)

**Duration:** 22–31 days
**Prerequisites:** V2 complete
**Why third:** Desktop shell is the primary user experience per `guide.md` §5.2.

#### V3 Phase-1: Tauri Desktop Shell + Embedded DB (10–14 days)

| Attribute | Value |
|-----------|-------|
| Risk | **HIGH** — platform-specific, embedded databases |
| Entry criteria | V2 complete |
| Exit criteria | `cortex` runs as desktop app. System tray shows status. Global hotkey opens command palette. |

**Deliverables:**
- Tauri 2.x shell
- Embedded PG
- Embedded vector store
- System tray
- Global hotkey
- Unix socket IPC

**Key files:**
- `src-tauri/` (new Rust crate)
- `backend/app/desktop/` (new)
- `backend/app/ipc/` (new)

---

#### V3 Phase-2: CLI TUI + Notifications + Native Integration (7–10 days)

| Attribute | Value |
|-----------|-------|
| Risk | Medium — platform-specific |
| Entry criteria | V3 Phase-1 complete |
| Exit criteria | TUI provides terminal UI. Desktop notifications work. |

**Deliverables:**
- Ink-based TUI
- Notification system
- Keyboard shortcuts
- Drag-and-drop
- Context menus

**Key files:**
- `cli/src/tui/` (new)
- Notification system

---

#### V3 Phase-3: Performance + Polish (5–7 days)

| Attribute | Value |
|-----------|-------|
| Risk | Low — optimization work |
| Entry criteria | V3 Phase-1-2 complete |
| Exit criteria | All performance targets met. Offline mode works. Cross-platform tested. |

**Deliverables:**
- Startup <3s
- Memory <200MB
- Offline mode
- Backup/restore
- Crash recovery

**Key files:** Optimization across existing files.

---

### V4: The Automaton (Automation)

**Duration:** 21–30 days
**Prerequisites:** V3 complete
**Why fourth:** Automation builds on stable daemon (V1) + extensible architecture (V2) + desktop (V3).

#### V4 Phase-1: Task Scheduler + Housekeeping (7–10 days)

| Attribute | Value |
|-----------|-------|
| Risk | Medium |
| Entry criteria | V3 complete |
| Exit criteria | Scheduled tasks execute on time. Housekeeping runs automatically. |

**Deliverables:**
- SchedulerEngine
- 7 housekeeping tasks
- Cron/event/webhook triggers
- Task history

**Key files:**
- `backend/app/services/scheduler/` (new)
- `backend/app/models/scheduled_task.py`

---

#### V4 Phase-2: MCP Server + Webhooks + Sessions (7–10 days)

| Attribute | Value |
|-----------|-------|
| Risk | Medium |
| Entry criteria | V4 Phase-1 complete |
| Exit criteria | Cortex exposes tools via MCP. Webhooks fire on events. Sessions persist. |

**Deliverables:**
- CortexMCPServer
- WebhookDispatcher
- SessionManager
- Agent-to-agent sessions

**Key files:**
- `backend/app/services/mcp_server/` (new)
- `backend/app/services/webhooks/` (new)
- `backend/app/services/sessions/` (new)

---

#### V4 Phase-3: Deep Research Engine + Integration Testing (7–10 days)

| Attribute | Value |
|-----------|-------|
| Risk | Medium |
| Entry criteria | V4 Phase-1-2 complete |
| Exit criteria | Agent can perform multi-step research. Reports generated. Integration tests pass. |

**Deliverables:**
- ResearchEngine
- Research tool for agent
- HTML/Markdown reports

**Key files:**
- `backend/app/services/research/` (new)

---

### V5: The Workspace (Daily Productivity)

**Duration:** 27–38 days
**Prerequisites:** V4 complete
**Why fifth:** Daily tools need stable daemon, automation, and MCP interop first.

#### V5 Phase-1: Email + Calendar (10–14 days)

| Attribute | Value |
|-----------|-------|
| Risk | **HIGH** — OAuth, multi-provider, IMAP/CalDAV |
| Entry criteria | V4 complete |
| Exit criteria | Email and calendar work via CLI and agent. OAuth flow completes. |

**Deliverables:**
- EmailProvider Protocol
- CalendarProvider Protocol
- OAuth 2.0 flow
- Local cache
- Agent tools

**Key files:**
- `backend/app/services/email/` (new)
- `backend/app/services/calendar/` (new)
- 5 agent tools

---

#### V5 Phase-2: Tasks + Notes + Documents (10–14 days)

| Attribute | Value |
|-----------|-------|
| Risk | Medium |
| Entry criteria | V5 Phase-1 complete |
| Exit criteria | CRUD operations work. Agent can manage tasks, notes, documents. |

**Deliverables:**
- Task system
- Notes system
- Document management
- 6 agent tools

**Key files:**
- `backend/app/services/tasks/` (new)
- `backend/app/services/notes/` (new)
- `backend/app/services/documents/` (new)

---

#### V5 Phase-3: Contacts + OpenAI API (7–10 days)

| Attribute | Value |
|-----------|-------|
| Risk | Low |
| Entry criteria | V5 Phase-1-2 complete |
| Exit criteria | Contacts work. OpenAI-compatible API serves requests. Dashboard shows workspace status. |

**Deliverables:**
- Contact system
- OpenAI-compatible endpoint
- Workspace dashboard
- Cross-tool workflows

**Key files:**
- `backend/app/services/contacts/` (new)
- `backend/app/api/v1/openai.py` (new)

---

### V6: The Ecosystem (Community + Polish)

**Duration:** 27–38 days
**Prerequisites:** V5 complete
**Why sixth:** Ecosystem and polish come after core is complete.

#### V6 Phase-1: Plugin Marketplace + Workflows (10–14 days)

| Attribute | Value |
|-----------|-------|
| Risk | **HIGH** — marketplace security, workflow DAG execution |
| Entry criteria | V5 complete |
| Exit criteria | Plugins installable from marketplace. Workflows execute correctly. |

**Deliverables:**
- PluginRegistry
- PluginSandbox
- WorkflowEngine
- Visual workflow editor
- Templates

**Key files:**
- `backend/app/services/marketplace/` (new)
- `backend/app/services/workflows/` (new)

---

#### V6 Phase-2: Graph Intelligence + Cross-Encoder (10–14 days)

| Attribute | Value |
|-----------|-------|
| Risk | **HIGH** — research-heavy, cross-encoder adds inference cost |
| Entry criteria | V6 Phase-1 complete |
| Exit criteria | Graph communities detected. Search quality >90%. Explainability panel works. |

**Deliverables:**
- GraphIntelligence (reasoning, communities, importance)
- CrossEncoderReranker
- 3-stage retrieval
- Search quality dashboard

**Key files:**
- `backend/app/services/graph/intelligence/` (new)
- `backend/app/services/retrieval/` (new)

---

#### V6 Phase-3: Polish + Launch (7–10 days)

| Attribute | Value |
|-----------|-------|
| Risk | Low — polish work |
| Entry criteria | V6 Phase-1-2 complete |
| Exit criteria | All benchmarks met. All pages pass accessibility. Documentation complete. Launch ready. |

**Deliverables:**
- Performance optimization
- WCAG 2.1 AA compliance
- Analytics
- Error reporting
- E2E tests
- Launch checklist

**Key files:** Optimization + accessibility across all files.

---

## 4. Testing Strategy

### Test Counts Per Version

| Version | Existing Tests | New Tests (Target) | Total |
|---------|---------------|-------------------|-------|
| V1 | 341 | 80+ | 421+ |
| V2 | 421+ | 180+ | 601+ |
| V3 | 601+ | 130+ | 731+ |
| V4 | 731+ | 160+ | 891+ |
| V5 | 891+ | 170+ | 1,061+ |
| V6 | 1,061+ | 170+ | 1,231+ |

### Test Infrastructure

- **Backend:** SQLite in-memory, 13 blanket-mocked services, transaction rollback
- **Frontend:** Vitest + jsdom + React Testing Library
- **Integration:** Feature flag tests for agent loop transition
- **E2E:** V6 adds full workflow tests

---

## 5. Risk Management

### Critical Risks

1. **Agent loop replacement** (V1 Phase-2): Feature flag. Old path available. Test against all 341 tests.
2. **Vector store abstraction** (V2): Protocol-only. No behavior change in V2. Desktop implementation in V3.
3. **Context compaction quality** (V1 Phase-2): Use cheaper model. Log events. Allow override.
4. **Scope creep** (V5): Strict phase ordering. Max 2 subsystems simultaneously.

### Mitigation Strategy

- Every risky change behind feature flag
- Old path + new path during transition
- All existing tests must pass with both flags
- Gradual rollout: new path handles new requests, old path handles existing runs

---

## 6. Documentation Maintenance

### After Each Phase

1. Update `versions/v{N}/progress.md` — mark phase complete
2. Update relevant `docs/` files if APIs changed
3. Run `make lint` + `make format`
4. Commit with descriptive message

### After Each Version

1. Update `implementation_steps.md` — mark version complete
2. Archive completed version plans to `_archive/`
3. Update `guide.md` if any principle changed

---

## 7. Getting Help

| Topic | Resource |
|-------|----------|
| Architecture questions | `guide.md` first |
| Phase details | `versions/v{N}/Phase-{M}.md` |
| Backend patterns | `CLAUDE.md` for commands and patterns |
| Frontend patterns | `DESIGN.md` for design system |
| Agent behavior | `AGENTS.md` for agent rules |
| Governance | `docs/GOVERNANCE.md` for workflow rules |
