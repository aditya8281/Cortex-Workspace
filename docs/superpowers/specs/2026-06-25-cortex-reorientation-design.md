# CORTEX Desktop-First Reorientation — Design Spec

**Date:** 2026-06-25
**Status:** Draft
**Scope:** Strategic reorientation of CORTEX from browser-first web application to desktop-first daemon-centric intelligence platform

---

## 1. Vision

CORTEX is a local-first persistent intelligence layer: a system that knows your files, code, conversations, projects, and habits, and maintains that understanding across sessions and technology changes. It is not primarily a chatbot, web application, or model wrapper — conversational interaction is one interface among many.

### Three Pillars

| Pillar | Meaning |
|--------|---------|
| **Persistent understanding** | CORTEX builds and maintains a coherent model of your digital life over time. It remembers what matters, forgets what doesn't, and surfaces relevant knowledge without being asked. |
| **Native integration** | CORTEX lives on your machine and integrates with how you already work — system tray, global hotkey, CLI, filesystem awareness. |
| **User sovereignty** | Everything runs locally. No telemetry, no cloud dependency, no vendor lock-in. The user chooses their model provider, storage backend, and interface. |

### What CORTEX Is

- A persistent intelligence daemon that maintains understanding over time
- A set of interchangeable interfaces (desktop shell, CLI, command palette, web UI, local API) over a shared intelligence layer
- A platform for autonomous agents that can plan, reason, search, write, and execute with user approval
- A system that runs any model (local or remote), stores data wherever the user chooses, and degrades gracefully when dependencies are unavailable

### What CORTEX Is Not

- Not primarily a chatbot — conversational interaction is one interface, not the product
- Not primarily a web application — the web UI is one surface among many, not the default
- Not a model wrapper — it does not add a thin UI over LLM APIs; it is an entire cognition layer with memory, reasoning, and agency
- Not a RAG platform — retrieval serves the deeper goal of persistent understanding
- Not cloud-dependent — everything runs locally by default

---

## 2. Product Definition

CORTEX is a persistent intelligence layer that lives on your machine. It maintains an evolving understanding of your digital life — files, code, conversations, projects, habits — and makes that understanding available through multiple surfaces.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Memory** | Persistent, decaying, confidence-weighted memory that accumulates with use. CORTEX remembers what matters. |
| **Understanding** | Maintains and updates understanding of your filesystem, codebase, projects, and digital life over time. |
| **Reasoning** | LLM-powered reasoning grounded in your actual files, conversations, and history — not generic knowledge. |
| **Agency** | Autonomous agents that plan, search, write, and execute under user supervision. |
| **Search** | Hybrid retrieval (vector + full-text + graph) across all indexed content. |
| **Knowledge Graph** | Entities, relationships, and connections across your digital world as an explicit service. |
| **Conversations** | Persistent chat history that feeds into memory and reasoning. |

### Interfaces (One Intelligence Layer, Many Surfaces)

All surfaces connect to the same daemon. No surface owns the intelligence.

| Surface | Primary Use | Priority |
|---------|-------------|----------|
| **Desktop shell** (Tauri) | Daily interaction, settings, visual memory browser | New build — high |
| **CLI** | Scripting, automation, power users | Complete stubs — high |
| **Command palette** (global hotkey) | Quick capture, search, trigger | New build — medium |
| **Web UI** (Next.js) | Remote access, complex visualizations | Maintain — low |
| **Local API** (FastAPI) | Integration, custom tooling, plugins | Versioned — keep |

### Operating Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Background** | Daemon always running, maintains understanding in real-time | Users who want always-on intelligence |
| **On-demand** | Daemon starts on trigger, sleeps after idle | Resource-conscious users |
| **Hybrid** | Core daemon always running, heavy work scheduled | Balanced approach |

### Audience

Developers, researchers, and power users who want a local intelligence layer that understands their work. Not a consumer chatbot product.

---

## 3. Architecture Direction

### Core Principle: Daemon-First, Not Browser-First

The current architecture (FastAPI ↔ Next.js ↔ PostgreSQL/Qdrant/Redis) was designed for a browser-first product. The target architecture is daemon-centric, with surfaces as interchangeable lenses into the intelligence layer.

### Target Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     SURFACE LAYER                          │
│  Desktop Shell  │  CLI  │  Cmd Palette  │  Web UI         │
│  (Tauri)        │       │  (global key)  │  (Next.js)      │
└──────────────────┴───────┴───────────────┴────────────────┘
                          │ IPC / REST / WebSocket
┌─────────────────────────▼────────────────────────────────┐
│              INTELLIGENCE DAEMON (cortexd)                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Event Bus (internal pub/sub)                        │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Job System (indexing, graph, embeddings, summary)   │ │
│  │  + Observability (tracing, history, metrics, diag)   │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Core Services                                       │ │
│  │  Memory │ RAG │ LLM │ Embedding │ Graph │ Search    │ │
│  │  Conversation │ Entity │ Index │ Agents             │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Service Abstraction Layer                           │ │
│  │  + Plugin/Extension Boundaries                       │ │
│  │  Embedded (in-process) ↔ Docker (containerized)      │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Daemon Lifecycle                                    │ │
│  │  Startup │ Shutdown │ Sleep/Wake │ Health │ Recovery │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────┬────────────────────────────────┘
                          │
     ┌────────────────────┼────────────────────┐
     ▼                    ▼                    ▼
  PostgreSQL          Qdrant                Redis
  (embedded or        (embedded or          (optional,
   Docker)             Docker)               fallback)
```

### 3.1 Intelligence Daemon (cortexd)

The current FastAPI backend is the kernel of the daemon. Its value — memory, RAG, agents, LLM integration, graph, entity extraction, search — is preserved. The shift is structural:

- **Current**: FastAPI app serving HTTP to a browser
- **Target**: Background daemon process with HTTP as one IPC channel

The daemon owns:
- All persistent state (memory, graph, index, conversations)
- All inference (embedding, LLM calls, retrieval)
- All background work (indexing, graph building, entity extraction)
- Process lifecycle (launch on boot, sleep when idle, wake on trigger)

**The daemon is the product.** UI surfaces are interchangeable lenses into it.

### 3.2 Event Bus

Internal pub/sub event bus decouples services:

- Services communicate through typed events, not direct imports
- Events: `file_changed`, `memory_decayed`, `index_complete`, `entity_discovered`, `conversation_archived`
- In-process by default (no external dependency)
- Observable: all events traced with metadata for debugging

### 3.3 Job System

Dedicated job/task system for background work:

- Jobs: indexing, graph construction, embeddings, summarization, memory maintenance
- Job persistence for restart recovery
- Queue with priority and scheduling
- Monitoring: job history, failure diagnostics, execution metrics

### 3.4 Service Abstraction Layer

Every backend service has a clean interface with swappable implementations:

| Service | Embedded Mode | Docker Mode | Fallback |
|---------|--------------|-------------|----------|
| Database | Embedded PostgreSQL (user-space) | PostgreSQL 16 | SQLite (read-only degraded) |
| Vector store | Embedded Qdrant | Qdrant | In-memory (degraded) |
| Cache | In-memory LRU | Redis 7 | None |
| LLM | llama.cpp / Ollama | Ollama | Mock |
| Embeddings | ONNX Runtime | Ollama | Deterministic mock |

**Decision needed**: Benchmark embedded PostgreSQL vs SQLite-first for default single-user desktop experience before committing to either.

### 3.5 Plugin/Extension Boundaries

Extension points defined during service abstraction (even if no plugins ship yet):

- Storage provider interface (filesystem, database, custom)
- LLM provider interface (already partially abstracted)
- Embedding provider interface (already three-tier)
- Event subscriber interface
- Tool/provider registration for agent system
- API surface is versioned to support third-party integrations without breakage

### 3.6 Daemon Lifecycle Management

| Operation | Behavior |
|-----------|----------|
| Startup | Dependency resolution, health checks, service initialization |
| Shutdown | Graceful drain, state flush, cleanup |
| Sleep | Pause background work, release memory, maintain minimal state |
| Wake | Resume background work, catch up on missed events |
| Health | Periodic self-check, dependency probing, recovery actions |
| Crash recovery | Journal replay, state reconciliation, safe restart |

### 3.7 OS Integration Layer

How the daemon interacts with the host OS:

- **Auto-launch**: User opt-in, systemd user unit / LaunchAgent
- **System tray**: Status icon, quick actions, mode toggle
- **Global hotkey**: Command palette summon, clipboard capture, quick search
- **Filesystem awareness**: Watched directories (partially implemented via file-watcher crate)
- **Resource management**: CPU/memory limits, battery-aware throttling
- **Notifications**: System notifications for completed work, triggers, reminders

### 3.8 Knowledge Graph as Explicit Service

The knowledge graph is an independent service boundary, separate from:

- Memory (long-term memory model with decay and confidence)
- Retrieval (hybrid search across vector + full-text + graph)
- Entity extraction (feeds into graph but is a distinct pipeline)

This separation prevents coupling between what CORTEX *remembers* (memory), what it *knows* (graph), and how it *finds* (retrieval).

### 3.9 API Versioning

- All endpoints already under `/api/v1/`
- Versioning contract: backward-compatible within major version
- Deprecation policy: one major version notice before removal
- Documented for third-party plugin and integration authors

---

## 4. Historical Archive Structure

### 4.1 `HISTORY.md` — Condensed Narrative

Single file at repo root. Readable in 5 minutes. Organized by milestones within June 2026:

```
# CORTEX Project History

## Timeline

### June 2: Project Inception
- Core architecture decisions: FastAPI + Next.js + PostgreSQL
- Cookie-based auth, two-password vault model
- Local-first principle established

### Early June: Identity, Storage, Memory, Indexing
- Multi-user authentication with JWT/refresh tokens
- Encrypted private vault per user (separate password)
- Profile management, admin user management
- Incremental indexer (hash-based change detection)
- Knowledge graph (graph_nodes, graph_edges)

### Mid June: Search, Retrieval, Graph, Conversations, Agents
- Cross-file search (vector + graph enrichment)
- Unified search API, repository management
- Agent system (base agent, planner, executor, RunManager)
- LLM provider abstraction (llama.cpp, Ollama)
- Model catalog with providers, variants, benchmarks
- Conversation-to-memory pipeline
- Long-term memory with decay, confidence, access tracking
- Hybrid retrieval (vector + keyword + graph + RRF + MMR)
- Semantic chunker, file watcher v2, batch indexer
- Agent SSE streaming, RAG pipeline, entity extraction

### Late June: Governance, Ecosystem, Consolidation
- Agentic ecosystem: governance docs, workflows, hooks, ADRs
- 68 agent skills, 11 validation hooks, 7 strategic commands
- Repository governance audit (5 doc systems consolidated → 1)
- Strategic command system (7 project commands for quality)
- Desktop-first reorientation decision (June 25)
- HISTORY.md created, docs/archive/ populated

## Key Architectural Decisions
(Curated list of every ADR with outcome, date, rationale)

## Lessons Learned
- Convention over configuration scales better than tool-first
- Multi-agent governance requires explicit docs, not implicit rules
- Desktop-first architecture avoids browser-origin constraints
- Embedded by default lowers adoption barrier significantly

## Deprecated Approaches
(What was tried and abandoned, with reasoning)
```

**Key message**: CORTEX evolved from concept to comprehensive intelligence platform within weeks, not years. This pace is the story worth telling.

### 4.2 `docs/archive/` — Verbatim Originals

Preserved verbatim, timestamped. No edits.

```
docs/archive/
├── README.md                         # Archive index with descriptions
├── 2026-06-24-agentic-ecosystem-spec.md
├── 2026-06-24-strategic-command-spec.md
├── 2026-06-24-strategic-command-plan.md
└── 2026-06-24-cortex-vision-pre-reorientation.md  (if README.md had prior content worth preserving)
```

### What Moves vs. What Stays

| Stays Active | Moves to Archive |
|-------------|------------------|
| `README.md` (condensed) | Previous iteration of README.md (if historically valuable) |
| `docs/ARCHITECTURE.md` (updated) | Prior architecture documents |
| `docs/ROADMAP.md` (cleaned — forward-looking only) | Old roadmap content with phase history |
| `docs/decisions/` (keep all ADRs) | — |
| `docs/superpowers/specs/` (keep current) | Superseded specs |
| `docs/agents/` (keep) | — |

### Impact on Current Docs

| Document | Action |
|----------|--------|
| `docs/ROADMAP.md` | Remove Phase 1–6.5 history. Reference HISTORY.md. Keep upcoming phases and improvement roadmap forward-looking. |
| `docs/ARCHITECTURE.md` | Update to reflect daemon-first architecture direction. Keep current diagrams but add target architecture layer. |
| `README.md` | Update vision statement to desktop-first. Keep condensed. |

---

## 5. Strategic Recommendations (Phased Migration)

A phased path from current codebase to target architecture. Phases are **capability milestones**, not calendar commitments. Each phase is complete when all deliverables are achieved, regardless of elapsed time. Priorities may shift as implementation reveals new constraints.

### Phase 1: Daemon Foundation

**Entry criteria**: Existing codebase stable, all tests passing.

**Deliverables:**
- `cortexd` entrypoint extracted from `backend/app/main.py`
- Daemon lifecycle: startup, shutdown, sleep/wake, health monitoring, service dependency management, crash recovery
- Local API: `/api/v1/` versioning established (most endpoints already compliant)
- API versioning contract documented
- Web UI continues to work exactly as before
- No user-visible changes — internal decoupling

**Exit criteria**: `cortexd start|stop|status` works. All existing tests pass. Web UI unchanged.

**Risk**: Low — refactoring and lifecycle wrappers around existing code.

### Phase 2: Service Abstraction

**Entry criteria**: Daemon lifecycle operational.

**Deliverables:**
- Service abstractions for: Database, Vector Store, Cache, LLM, Embeddings
- Existing implementations moved behind interfaces
- Plugin/extension boundaries defined: storage provider, LLM provider, embedding provider, event subscriber, agent tool/provider, API surface
- Benchmark: SQLite vs embedded PostgreSQL for single-user desktop experience
- Plugin/implementation contract documented

**Exit criteria**: Services swappable via config. Plugin boundaries documented. Benchmark results recorded.

**Risk**: Medium — interface design requires foresight. Boundaries kept minimal.

### Phase 3: Event Bus & Job System

**Entry criteria**: Service abstractions in place.

**Deliverables:**
- In-process event bus (pub/sub, no external dependency)
- Job system for background work: indexing, graph building, embeddings, summarization, memory maintenance
- Job persistence for restart recovery
- Observability: event tracing, job history, failure diagnostics, execution metrics
- Knowledge Graph becomes explicit service boundary (separate from memory and retrieval)
- Services communicate via events instead of direct coupling

**Exit criteria**: Background jobs survive restart. Events observable via tracing. Knowledge Graph independently queryable.

**Risk**: Medium — new patterns, but bounded and composable.

### Phase 4: CLI Completion

**Entry criteria**: Daemon operational (can begin parallel to Phase 2–3).

**Deliverables:**
- All 15 command stubs implemented
- CLI connects to daemon via local API (HTTP or Unix socket)
- Key commands: `cortex search`, `cortex remember`, `cortex status`, `cortex agent`, `cortex config`

**Exit criteria**: CLI is a complete functional interface for daily use.

**Risk**: Low — existing scaffold, implementation work only.

### Phase 5: API Stabilization

**Entry criteria**: Service abstractions in place, CLI using API.

**Deliverables:**
- API contract hardened based on real usage from CLI and services
- Deprecation policy documented: one major version notice before removal
- API documentation published for third-party integration authors
- Backward compatibility verified across all endpoints

**Exit criteria**: API documented, stable, and versioned. Deprecation policy published.

**Risk**: Low — convention and documentation work.

### Phase 6: Desktop Shell

**Entry criteria**: API stable, daemon lifecycle proven.

**Deliverables:**
- Tauri shell connecting to daemon
- System tray with status, quick actions, settings
- Global hotkey for command palette (search, capture, trigger)
- Desktop notifications for background work and triggers
- Current web UI remains fully functional alongside

**Exit criteria**: Daily use possible entirely through desktop shell without browser.

**Risk**: High — new platform, new build system, Tauri learning curve.

### Phase 7: Web UI Transition

**Entry criteria**: Desktop shell functional for daily use.

**Deliverables:**
- No new major features in web UI
- Bug fixes and security updates only
- All new features go to desktop shell or CLI first
- Web UI remains fully functional for remote access scenarios

**Exit criteria**: Web UI maintained but no longer primary development target.

**Risk**: Low — reduction of scope, not expansion.

### Phase Summary

| Phase | Deliverables | Dependencies | Risk |
|-------|-------------|--------------|------|
| 1. Daemon Foundation | `cortexd` entrypoint, lifecycle, API versioning | None (current codebase) | Low |
| 2. Service Abstraction | Swappable interfaces, plugin boundaries, SQLite benchmark | Phase 1 | Medium |
| 3. Event Bus & Job System | Event bus, job system, observability, KG boundary | Phase 2 | Medium |
| 4. CLI Completion | 15 CLI commands implemented | Phase 1 (parallel to 2–3) | Low |
| 5. API Stabilization | Hardened contract, deprecation policy, docs | Phase 2 + 4 | Low |
| 6. Desktop Shell | Tauri shell, system tray, hotkey, notifications | Phase 1 + 5 | High |
| 7. Web UI Transition | Maintain-only mode for web UI | Phase 6 | Low |

### Phase Dependency Graph

```
Phase 1 (Daemon Foundation) — no dependencies
  ├── Phase 2 (Service Abstraction)
  │    └── Phase 3 (Event Bus & Job System)
  │         └── Phase 5 (API Stabilization)
  │              └── Phase 6 (Desktop Shell)
  │                   └── Phase 7 (Web UI Transition)
  └── Phase 4 (CLI Completion) — can start parallel to Phase 2–3
```

---

## 6. Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Daemon-first, surface-second** | Intelligence must work without UI. CLI-only operation is a valid mode. |
| **Abstract, don't replace** | Current backend is the daemon kernel. Refactor boundaries, don't discard. |
| **Embedded by default, Docker for power** | Zero-install experience for newcomers. Docker for those who need scale. |
| **Event bus for service coupling** | Direct imports create implicit dependencies. Events create decoupled, observable services. |
| **Dedicated job system** | Background work needs persistence, retry, monitoring — not fire-and-forget. |
| **Knowledge Graph as separate service** | Prevents coupling between memory, retrieval, and entity relationships. |
| **API versioning from the start** | Inexpensive now, expensive later once CLI, desktop, and third-party integrations exist. |
| **Plugin boundaries during abstraction** | Defining extension points before plugins exist ensures clean interfaces without retrofitting. |
| **Tauri for desktop shell** | Rust ecosystem alignment, existing crates, smaller binaries than Electron. |
| **CLI as primary automation interface** | Automation, scripting, CI/CD — CLI is the programmable surface. |
| **Web UI as secondary surface** | Remote access, complex visualizations. No longer the primary experience. |

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Desktop-first shift dilutes existing web experience | Medium | Maintain web UI through transition; reduce scope, don't abandon |
| Tauri complexity slows desktop delivery | High | Prove shell with minimal surface first (system tray + hotkey only) |
| Service abstraction adds overhead | Low | Keep interfaces thin; refactor only what needs swapping |
| SQLite may not meet requirements | Medium | Benchmark early in Phase 2; embedded PostgreSQL is safe fallback |
| Event bus introduces latency for in-process calls | Low | Bus is in-process; cost is function call overhead |
| Too many phases overwhelm development | Medium | Phases are capability milestones, not deadlines; priorities shift |

---

## 8. Verification

After any implementation phase:
1. All existing tests still pass
2. Web UI continues to function (during transition)
3. Daemon lifecycle: start, stop, restart, sleep, wake all work
4. CLI connects to daemon and returns correct results
5. Tauri shell (when built) connects to daemon and shows correct state
6. API versioning: old endpoints still work after new versions
7. No regressions in memory, search, conversation, or agent functionality
