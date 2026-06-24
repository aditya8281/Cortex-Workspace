# CORTEX Constitution

**Date:** 2026-06-25
**Purpose:** The definitive statement of what Cortex is, what it becomes, and the principles that govern every decision. This is the final destination. Everything else is implementation detail.

---

## 1. Vision

CORTEX is a local-first persistent intelligence layer: a system that knows your files, code, conversations, projects, and habits, and maintains that understanding across sessions and technology changes.

It is not primarily a chatbot, web application, or model wrapper. Conversational interaction is one interface among many. The intelligence layer is the product.

### Three Pillars

| Pillar | Meaning |
|--------|---------|
| **Persistent understanding** | CORTEX builds and maintains a coherent model of your digital life over time. It remembers what matters, forgets what doesn't, and surfaces relevant knowledge without being asked. |
| **Native integration** | CORTEX lives on your machine and integrates with how you already work — system tray, global hotkey, CLI, filesystem awareness. It degrades gracefully and never forces a workflow. |
| **User sovereignty** | Everything runs locally. No telemetry, no cloud dependency, no vendor lock-in. The user chooses their model provider, storage backend, and interface. Data never leaves the machine unless the user explicitly sends it. |

### What CORTEX Is

- A persistent intelligence daemon that maintains understanding over time
- A set of interchangeable interfaces over a shared intelligence layer
- A platform for autonomous agents that can plan, reason, search, write, and execute with user approval
- A system that runs any model (local or remote), stores data wherever the user chooses, and degrades gracefully when dependencies are unavailable
- A complete AI workspace: code intelligence, memory, knowledge graph, daily productivity tools, and automation

### What CORTEX Is Not

- Not primarily a chatbot — conversational interaction is one interface, not the product
- Not primarily a web application — the web UI is one surface among many, not the default
- Not a model wrapper — it does not add a thin UI over LLM APIs; it is an entire cognition layer with memory, reasoning, and agency
- Not a RAG platform — retrieval serves the deeper goal of persistent understanding
- Not cloud-dependent — everything runs locally by default
- Not a single-purpose tool — it is an ecosystem that grows with the user

---

## 2. End State

CORTEX at its destination is a daemon process (`cortexd`) that:

1. **Runs in the background** on the user's machine, maintaining persistent understanding
2. **Provides intelligence** through memory, reasoning, search, knowledge graph, and agent capabilities
3. **Connects through any surface** — desktop shell, CLI, command palette, web UI, local API
4. **Degrades gracefully** — embedded databases by default, Docker for power users, in-memory fallbacks when services are unavailable
5. **Extends through plugins** — providers, tools, and pipelines can be added without forking
6. **Interoperates** via MCP — both consuming external tools and exposing its own
7. **Automates** — task scheduling, housekeeping, webhooks, autonomous operation
8. **Manages daily life** — email, calendar, tasks, notes, documents, contacts — not just code

The intelligence layer is permanent. The surfaces are interchangeable. The daemon is the product.

---

## 3. Core Principles

These principles are non-negotiable. Every architectural decision, every feature, every trade-off must satisfy them.

### 3.1 Local-First

All data, all inference, all storage happens on the user's machine. No feature requires cloud connectivity. No telemetry. No external calls without explicit user action. The system works fully offline.

**Consequence:** Embedded databases are the default. Docker is optional. LLM providers can be local (Ollama, llama.cpp) or remote (user's choice).

### 3.2 Graceful Degradation

Every service has a fallback. If Redis is unavailable, use in-memory. If Qdrant is unavailable, use in-memory vectors. If no LLM is configured, fall back to keyword matching. The system never crashes because a dependency is missing — it operates at reduced capacity.

**Consequence:** Every new service must define its fallback before implementation begins.

### 3.3 Daemon-First, Surface-Second

The daemon owns all intelligence. Surfaces are interchangeable lenses. No surface owns the data or the logic. The system must be fully operational through CLI alone — no browser, no desktop shell required.

**Consequence:** Every capability must be accessible through the API, which the CLI uses directly.

### 3.4 Separation of Concerns

Memory is not retrieval. Retrieval is not the knowledge graph. The graph is not entity extraction. Each is an independent service boundary with its own interface. Services communicate through events, not direct imports.

**Consequence:** No service imports another service's internals. All communication through typed events or explicit interfaces.

### 3.5 Plugin Boundaries Early

Define extension points before plugins exist. Every major service has a Protocol interface. Implementations are swappable. The community can add providers, tools, and pipelines without modifying core code.

**Consequence:** Python Protocol classes define every service boundary. First implementation ships behind the interface.

### 3.6 Evidence Over Opinion

Every architectural decision must cite evidence. Current state is verified against code. Reference repository patterns are validated against actual implementations. Claims without evidence are rejected.

**Consequence:** The council deliverables are the ground truth. Design decisions reference them.

### 3.7 Incremental Safety

Every change must pass all existing tests. No breaking changes without migration paths. Feature flags for risky changes. Gradual rollout. The system is always deployable.

**Consequence:** TDD for all new subsystems. Feature flags for agent loop replacement. Parallel old+new paths during transition.

---

## 4. Architecture Principles

### 4.1 Daemon Architecture

**Current approach:** FastAPI app serving HTTP to a browser. Two-password auth. PostgreSQL + Redis + Qdrant in Docker. 26+ services tightly coupled through imports.

**Reference repo approaches:**
- Odysseus: Server-side runs with replay buffer, 180s grace period, persistent state
- Continue: In-process daemon with AbortController for cancellation
- Open WebUI: Containerized but with persistent volumes for all state

**Final decision:**

The daemon (`cortexd`) is the FastAPI backend refactored into a background process with lifecycle management. Not a rewrite. A structural evolution.

| Aspect | Decision |
|--------|----------|
| Process model | Single async process (uvicorn) with lifecycle hooks |
| Lifecycle | start → run → sleep → wake → shutdown → crash recovery |
| State | All persistent state in PostgreSQL. All ephemeral state in Redis or in-memory. |
| IPC | HTTP/REST (existing), WebSocket (existing), Unix socket (new for CLI/daemon) |
| Health | Periodic self-check. Dependency probing. Recovery actions. |
| Crash recovery | Journal-based replay. State reconciliation. Safe restart with PID lock. |

**What changes:** The FastAPI app gains a `cortexd` entrypoint with lifecycle management. PID file. Health checks. Sleep/wake. Graceful shutdown with drain.

**What stays:** The existing service layer, API routes, auth, middleware — all preserved. The daemon is the existing backend wrapped in lifecycle management.

### 4.2 Desktop Architecture

**Current approach:** Next.js web UI. No desktop presence. Browser-only.

**Reference repo approaches:**
- Odysseus: PyInstaller portable (simple but limited)
- Continue: VS Code extension (IDE-bound, not standalone)
- Open WebUI: Browser-only (same as current Cortex)

**Final decision:**

Tauri shell for desktop integration. Not a full application — a thin shell that connects to the daemon.

| Surface | Role | Priority |
|---------|------|----------|
| System tray | Status, quick actions, mode toggle | High |
| Global hotkey | Command palette (search, capture, trigger) | High |
| Settings | Configuration, provider selection, vault management | Medium |
| Memory browser | Visual exploration of memory, graph, search results | Low |

**What changes:** New Tauri crate. System tray integration. Global hotkey registration. IPC to daemon.

**What stays:** Web UI remains fully functional. CLI works independently. Desktop shell is additive, not replacing.

**Design constraint:** The desktop shell contains zero business logic. It is a presentation layer that talks to the daemon API. If the daemon is down, the shell shows status — it does not attempt to work around it.

### 4.3 Memory Architecture

**Current approach:** Confidence-based scoring with time-based decay. Basic CRUD. No consolidation, no deduplication, no contradiction detection. Embedding cache with TTL.

**Reference repo approaches:**
- Mem0 V3: Two-phase extraction (ADD-only + consolidation), 3-level dedup, entity boosting
- Graphiti: Temporal KG with LLM extraction, contradiction detection + invalidation, bi-temporal tracking
- Continue: Session memory with relevance scoring

**Final decision:**

Memory is an independent service boundary. It accumulates facts, scores confidence, detects contradictions, consolidates duplicates, and decays over time.

| Aspect | Decision |
|--------|----------|
| Extraction | LLM-based (replaces regex). Two-phase: extract → consolidate. |
| Storage | PostgreSQL `long_term_memory` table with `valid_at`/`invalid_at` for bi-temporal tracking |
| Confidence | Keep Cortex's unique confidence scoring (0.95x/30d decay). Add access-count reinforcement. |
| Deduplication | Mem0 V3 three-level: batch-level, vector-similarity, hash-exact |
| Contradiction | Graphiti pattern: when new fact contradicts existing, invalidate old with `invalid_at` timestamp |
| Consolidation | Pipeline: extract → dedup → contradiction check → merge → confidence assign → decay |
| Retrieval | Memory results feed into hybrid retrieval. Entity boosting from consolidated memories. |

**What stays:** Confidence scoring. Time-based decay. Access-count reinforcement. Embedding cache.

**What changes:** Regex extraction → LLM extraction. No dedup → 3-level dedup. No contradiction detection → invalidation timestamps. No consolidation → automated pipeline.

**Key principle:** Memory is what CORTEX *remembers*. It is separate from the knowledge graph (what it *knows*) and retrieval (how it *finds*). These three are independent service boundaries that compose, not one monolithic system.

### 4.4 Graph Architecture

**Current approach:** Code-aware graph building from import/call/inheritance edges. Regex-based entity extraction. Graph results merged into hybrid retrieval via RRF. Unique capability — no reference repo does this.

**Reference repo approaches:**
- Graphiti: Temporal KG with LLM extraction, contradiction detection, community detection, multi-hop traversal
- Mem0: Entity store with vector search but no graph traversal
- LlamaIndex: Property graph index with LLM extraction, community detection

**Final decision:**

The knowledge graph is an explicit service boundary, separate from memory and retrieval.

| Aspect | Decision |
|--------|----------|
| Entity extraction | LLM-based (replaces regex). Works for code AND non-code content. |
| Edge types | Keep import/call/inheritance for code. Add general relationship types for non-code. |
| Temporal | Valid/invalid timestamps on edges. Facts expire when contradicted. |
| Retrieval | Graph results feed into hybrid retrieval via RRF (existing pattern, proven). |
| Community detection | Defer. Requires richer entity graph first. |
| Multi-hop traversal | Defer. Requires graph DB optimization. |

**What stays:** Code-aware graph building (unique capability). Graph-enhanced retrieval via RRF. GraphNode/GraphEdge models.

**What changes:** Regex entity extraction → LLM-based extraction. Code-only → universal (conversations, documents, emails). No temporal tracking → valid/invalid timestamps.

**Key principle:** The graph is what CORTEX *knows*. Facts about entities and their relationships. This is different from memory (what it *remembers* — confidence-weighted, decaying facts) and retrieval (how it *finds* — vector + fulltext + graph search).

### 4.5 Retrieval Architecture

**Current approach:** HybridRetrievalV2 — three sources (vector + fulltext + graph) merged via RRF with MMR diversity reranking. Token-budgeted context injection. Retrieval metrics. Best-in-class among all reference repos.

**Reference repo approaches:**
- Mem0: Triple-signal (vector + BM25 + knowledge graph) with adaptive normalization and entity boosting
- Graphiti: Composable recipes with MMR diversity, entity-level reranking
- LlamaIndex: 70+ vector backends, composable RAG pipelines, response synthesis
- Continue: IContextProvider pattern — 20+ composable, token-budgeted context sources

**Final decision:**

Retrieval is the final stage — it finds and ranks relevant content for the agent or user. It composes memory, graph, and search results.

| Aspect | Decision |
|--------|----------|
| Sources | Vector + fulltext + graph (keep). Add memory as 4th source when consolidated. |
| Fusion | RRF (keep). Add adaptive score normalization (Mem0 pattern) for cross-source alignment. |
| Reranking | MMR diversity (keep). Add entity boosting (Mem0 pattern) for context-aware ranking. |
| Context providers | Continue pattern: composable, token-budgeted sources that contribute to agent context. |
| Recipes | Composable search recipes (Graphiti pattern) for different search modes (code, semantic, graph-first). |
| Cross-encoder | Defer. Requires GPU or API dependency. |

**What stays:** Three-source hybrid retrieval. RRF fusion. MMR diversity. Token budgeting. Retrieval metrics. Code-aware chunking. Semantic chunking.

**What changes:** Monolithic pipeline → composable context providers. Fixed scoring → adaptive normalization. No entity boosting → entity-aware ranking. Three sources → four (memory added as consolidation matures).

**Key principle:** Retrieval is how CORTEX *finds*. It is the lens through which the agent and user access the intelligence layer. It should be adaptive, composable, and quality-measured.

### 4.6 Agent Architecture

**Current approach:** Planner→Executor two-agent pattern. 5 tools with no schemas. No compaction. No prompt security. No MCP. No detached runs. No intent classification. No loop-breaker. This is the weakest subsystem across all reference repos.

**Reference repo approaches:**
- Odysseus: 3,485-line streaming agent loop. 30+ tools with JSON Schema. Auto-compaction at 85%. UNTRUSTED_SOURCE_DATA guards. Intent classification. Stall detection. Fresh-context completion verifier. Detached runs with replay buffer.
- Continue: Single tool-calling loop. 18 tools. Auto-compaction. IContextProvider. AbortController.
- Strands: Single execution loop. @tool decorator with auto-schema. MCPTool wrapper. Swarm orchestration. Workflow DAGs.

**Final decision:**

Single streaming agent loop. Replaces Planner→Executor entirely.

| Aspect | Decision |
|--------|----------|
| Architecture | Single async generator streaming loop (Odysseus pattern, adapted) |
| Tools | @tool decorator with auto-generated JSON Schema from type hints + docstrings |
| Tool policy | Per-turn composition: allow/deny/ask per tool. Replaces HMAC approval tokens. |
| Context | Auto-compaction at 85% with Goal/Done/State/Pending structured summary |
| Security | UNTRUSTED_SOURCE_DATA markers on all external content entering prompts |
| Intent | Casual/admin/agent/continuation classification before entering loop |
| Stall detection | Loop-breaker: detect repeated identical calls, force answer |
| Completion | Fresh-context LLM verifier subagent |
| Detached runs | Server-side persistence with replay buffer, PID tracking, orphan detection |
| Planning | Planner becomes a tool, not a separate agent. "Plan this task" is a tool call. |
| Max iterations | 25 (configurable), with stall detection as primary loop control |

**What stays:** Tool security (SSRF, path traversal, blocked commands). Workspace sandboxing. AgentRun/AgentStep models. SSE streaming. Background execution.

**What changes:** Two-agent → single agent. 5 tools → 30+. No schemas → full JSON Schema. No compaction → auto at 85%. No security markers → UNTRUSTED_SOURCE_DATA. No intent classification → 4-way routing. No stall detection → loop-breaker. No completion verification → fresh-context verifier. No persistence → server-side runs with replay.

**Key principle:** The agent is what CORTEX *does*. It plans, reasons, searches, writes, and executes under user supervision. The agent loop is the central nervous system — everything else serves it or is served by it.

**Critical risk:** Replacing the agent loop breaks the central nervous system. Mitigation: feature flag, keep planner.py as fallback, test against all 341 existing tests, gradual migration with old path available during transition.

### 4.7 Workflow Architecture

**Current approach:** Background tasks (arq + Redis) for indexing, embedding, graph building. In-memory asyncio.Queue for SSE. No persistence. Tasks die with the process.

**Reference repo approaches:**
- Odysseus: Event bus + task scheduler. Cron/event/webhook triggers. 10 built-in housekeeping tasks. Personal assistant CrewMember.
- Continue: AbortController for cancellation. No background task system.
- Strands: Workflow DAGs for multi-agent orchestration.

**Final decision:**

Two-tier job system: lightweight event bus + persistent job queue.

| Tier | Purpose | Implementation |
|------|---------|---------------|
| Event bus | Decoupled service communication, in-process pub/sub | In-process, no external dependency |
| Job queue | Persistent background work (indexing, graph, embeddings, summarization) | arq + Redis (existing), with persistence for restart recovery |

| Aspect | Decision |
|--------|----------|
| Event types | file_changed, memory_decayed, index_complete, entity_discovered, conversation_archived |
| Event bus | In-process pub/sub. Observable with tracing. No external dependency. |
| Job persistence | Jobs survive restart. Replay on recovery. Priority queue. |
| Task scheduler | Cron/event/webhook triggers for autonomous operation |
| Housekeeping | Automatic: memory decay, embedding refresh, graph maintenance, staleness detection |

**What stays:** arq + Redis for heavy background work. SSE for real-time streaming. AgentRun/AgentStep for execution tracking.

**What changes:** In-memory Queue → persistent job queue. Direct service imports → event-driven communication. No task persistence → jobs survive restart. No scheduling → cron/event/webhook triggers.

**Key principle:** Workflows are how CORTEX *operates autonomously*. Background work must be reliable, observable, and restart-safe.

### 4.8 Plugin Architecture

**Current approach:** No extension points. All capabilities hardcoded. Can't add providers, tools, or pipelines without forking.

**Reference repo approaches:**
- Open WebUI: 6-layer system (models, prompts, tools, functions, pipelines, auth)
- AnythingLLM: 5-layer system (LLM, embedding, vector, document, web scraper)
- Strands: @tool decorator with dynamic loading. MCPTool wrapper.
- LlamaIndex: 70+ backends via connector pattern

**Final decision:**

Three-layer plugin architecture using Python Protocol classes.

| Layer | Purpose | Extension Points |
|-------|---------|-----------------|
| Layer 1: Providers | LLM, embedding, vector store | Protocol interfaces with factory registration |
| Layer 2: Tools | Agent tools (function-calling) | @tool decorator + MCP-compatible tool wrapping |
| Layer 3: Pipelines | Processing chains (indexing, consolidation, retrieval) | Composable pipeline stages |

| Aspect | Decision |
|--------|----------|
| Interface | Python Protocol (structural subtyping, not ABC inheritance) |
| Registration | Decorator-based. `@register_provider("llm", "ollama")` |
| Discovery | Filesystem scan of `~/.cortex/plugins/` + MCP tool discovery |
| Versioning | Plugin API versioned. Breaking changes require major version bump. |
| Loading | Lazy loading. Plugins loaded on first use, not at startup. |
| Isolation | Plugins run in daemon process. No sandboxing initially (trust model). |

**What stays:** Existing service constructors. Three-tier embedding fallback. LLM provider routing.

**What changes:** Hardcoded providers → Protocol interfaces. No extension → decorator registration. Monolithic services → composable pipelines.

### 4.9 CLI Architecture

**Current approach:** 15 Commander.js stubs. Zero functionality. 158 lines total.

**Reference repo approaches:**
- Continue: Working CLI with headless + Ink TUI
- Odysseus: 20+ specialized CLIs
- Open WebUI: No CLI

**Final decision:**

CLI is the primary automation interface. It connects to the daemon via local API (HTTP or Unix socket).

| Command Group | Commands | Priority |
|--------------|----------|----------|
| Daemon | start, stop, status, logs | Critical |
| Agent | run, chat, list, cancel | Critical |
| Search | search, index, status | High |
| Memory | remember, recall, forget, status | High |
| Config | set, get, list | High |
| Vault | lock, unlock, status | Medium |
| Knowledge | graph, entities, relationships | Medium |

| Aspect | Decision |
|--------|----------|
| Implementation | Commander.js (existing scaffold). All stubs become real commands. |
| Connection | HTTP to daemon API. Unix socket for local-only. |
| Output | JSON (default) + human-readable (when attached to terminal) |
| TUI | Defer. Start with headless. Add Ink TUI after headless is stable. |
| Scriptability | Every command returns exit code + JSON. Piping, jq integration. |

**What stays:** Commander.js routing (15 commands wired). TypeScript/Node.js runtime.

**What changes:** 15 stubs → 15 working commands. Zero lines of logic → full daemon management.

### 4.10 Ecosystem Architecture

**Current approach:** No MCP. No external tool integration. No plugin system. 12 governance rules, 11 hooks, 10 workflows, 7 strategic commands. Governance is unmatched but ecosystem is closed.

**Reference repo approaches:**
- Odysseus: Full MCP manager (stdio + SSE). External tool consumption.
- Continue: MCPManagerSingleton. MCP as primary extension mechanism.
- Strands: MCPTool wrapper. External tool consumption.
- AnythingLLM: MCP hypervisor. Bidirectional.

**Final decision:**

Ecosystem is built on three pillars: MCP interop, plugin system, and governance.

| Pillar | Decision |
|--------|----------|
| MCP client | Full MCP manager. stdio + SSE transports. Lifecycle management. |
| MCP server | Expose Cortex tools to other MCP clients. Deferred to after client is stable. |
| MCP tool wrapping | External MCP tools appear as native Cortex tools via MCPTool wrapper |
| Plugin ecosystem | Three-layer plugins (providers, tools, pipelines) for community contribution |
| Governance | Keep all 12 rules, 11 hooks, 10 workflows, 7 commands. Add effectiveness metrics. |
| API versioning | `/api/v1/` with backward compatibility contract. Deprecation policy. |
| OpenAI-compatible API | Expose Cortex as OpenAI-compatible endpoint for external tool integration |

**What stays:** All governance. All hooks. All workflows. All strategic commands. API versioning.

**What changes:** Zero MCP → full MCP client + server. Closed ecosystem → open plugin system. No external integration → OpenAI-compatible API.

---

## 5. Product Principles

### 5.1 Intelligence Over Interface

The intelligence layer is the product. Interfaces are interchangeable. A feature that only works in one interface is a bug. Every capability must be accessible through every surface.

### 5.2 Desktop-First, Web-Compatible

The default experience is desktop. The web UI is maintained for remote access but is no longer the primary development target. New features go to desktop shell or CLI first, then web UI if needed.

### 5.3 CLI as Programmable Surface

The CLI is the automation interface. Every daemon operation is scriptable. JSON output. Exit codes. Piping. This is how power users and CI/CD systems interact with CORTEX.

### 5.4 Graceful Degradation Over Hard Requirements

If a dependency is missing, operate at reduced capacity. Never crash. Never refuse to start. The system should work with zero configuration — just a machine with Python and Node.js.

### 5.5 Embedded by Default, Docker for Power

The default installation uses embedded databases (user-space PostgreSQL, in-process vectors). Docker is optional for users who need scale or already run containers.

### 5.6 One Source of Truth Per Topic

Documentation follows the single-source-of-truth hierarchy:
- README.md: public-facing project overview
- CLAUDE.md: AI agent development guidance
- docs/ARCHITECTURE.md: system architecture
- docs/ROADMAP.md: development roadmap
- docs/GOVERNANCE.md: ecosystem governance
- .agents/plans/: active plans only (archive completed ones)

No topic is documented in two places. Cross-references point to the source, never duplicate.

---

## 6. UX Principles

### 6.1 Surfaces Are Lenses

Desktop shell, CLI, command palette, web UI — all are views into the same intelligence layer. State is consistent across surfaces. No surface owns the data.

### 6.2 Invisible Until Needed

The daemon runs silently. No notifications unless something requires attention. No popups. No interruptions. The user invokes CORTEX when they want it, not when it wants attention.

### 6.3 Immediate Feedback

Every action gets immediate feedback. SSE streaming for agent responses. Progress indicators for long operations. Status updates for background jobs. No dead air.

### 6.4 Command Palette as Primary Interaction

The global hotkey command palette is the fastest way to interact: search, capture, trigger, ask. It appears instantly. It searches everything. It does everything.

### 6.5 Web UI for Complex Visualization

The web UI is for things that need visual space: memory browser, graph visualization, model comparison, document viewer. It is not for daily interaction.

### 6.6 Consistent Design Language

"Warm Neural Dark" theme. Dark-only glassmorphism. Cyan accent. Neural network animated background. Every surface uses the same design tokens.

---

## 7. Desktop Principles

### 7.1 Shell Contains Zero Logic

The Tauri desktop shell is a presentation layer. It connects to the daemon API. It displays state. It sends commands. It contains no business logic, no data processing, no intelligence.

### 7.2 System Tray Is Always Available

The system tray icon shows daemon status. Quick actions: search, remember, ask. Mode toggle: background/on-demand/hybrid. This is the minimal interaction surface.

### 7.3 Global Hotkey Is Instant

The command palette appears in <100ms. It searches across all indexed content. It accepts natural language. It triggers agent actions. This is the power user's primary interface.

### 7.4 Desktop Notifications Are Opt-In

System notifications for: completed background jobs, agent task completion, reminders, webhook triggers. User controls which notifications are shown.

### 7.5 Resource Management Is Conscious

CPU/memory limits for the daemon. Battery-aware throttling on laptops. Sleep when idle. Wake on trigger. The daemon respects the machine it runs on.

---

## 8. Memory Principles

### 8.1 Memory Decays Unless Reinforced

Every memory has a confidence score. Confidence decays over time (0.95x per 30 days). Access reinforces. The system naturally forgets what isn't used and remembers what matters.

### 8.2 New Facts Compete With Old Facts

When a new fact contradicts an existing memory, the old one is invalidated (not deleted). Both are preserved with valid/invalid timestamps. The system understands that knowledge changes over time.

### 8.3 Deduplication Is Automatic

Three levels: batch-level within extraction, vector-similarity against existing memories, hash-based exact match. The user never sees duplicate memories.

### 8.4 Memory Feeds Retrieval

Consolidated memories contribute to hybrid retrieval. Entity boosting from memory improves search ranking. The memory system and the retrieval system are composed, not coupled.

### 8.5 Extraction Is LLM-Based

Regex extraction is replaced by LLM-based extraction. The LLM understands context, nuance, and implicit relationships that regex cannot capture. Extraction quality directly affects memory quality.

---

## 9. Graph Principles

### 9.1 Graph Is Independent From Memory

Memory is what CORTEX *remembers* (confidence-weighted, decaying facts). The graph is what it *knows* (entities and relationships). These are separate service boundaries that compose through retrieval.

### 9.2 Graph Is Universal

The graph covers code (import/call/inheritance), conversations (speaker/topic/reference), documents (entity/relationship), emails (sender/topic/thread), and everything else. Not just code.

### 9.3 Graph Is Temporal

Edges have valid/invalid timestamps. Facts expire when contradicted. The graph understands that knowledge changes over time.

### 9.4 Graph Feeds Retrieval

Graph results are a source in hybrid retrieval. Graph traversal provides related entities. Graph structure improves search ranking. The graph and retrieval compose, not couple.

---

## 10. Agent Principles

### 10.1 Single Loop, Not Multi-Agent

One streaming agent loop handles all user interactions. Planning is a tool call, not a separate agent. Execution is the loop itself. No Planner→Executor separation.

### 10.2 Tools Have Schemas

Every tool has a JSON Schema generated from type hints and docstrings. The LLM knows exactly what arguments tools accept. Tools are defined with `@tool` decorator.

### 10.3 Tool Policy Is Per-Turn

Every turn, the agent can allow, deny, or require approval for specific tools. This replaces HMAC approval tokens. Policy is composable and configurable.

### 10.4 Context Is Managed

Auto-compaction at 85% of context window. Structured summary: Goal/Done/State/Pending. The agent never loses context in long conversations.

### 10.5 External Content Is Guarded

All external content (retrieval results, file contents, search results, MCP tool outputs) enters prompts wrapped in UNTRUSTED_SOURCE_DATA markers. The agent knows what it can trust.

### 10.6 Intent Is Classified

User input is classified before entering the agent loop: casual (fast path, no LLM), admin (configuration), agent (full loop), continuation (resume previous). Wasted LLM calls are eliminated.

### 10.7 Stalls Are Detected

The loop-breaker detects repeated identical tool calls and forces an answer. No more agent stuck in infinite loops. Stall detection is the primary loop control, not max iterations.

### 10.8 Completion Is Verified

A fresh-context LLM subagent verifies that the task was actually completed. The verifier has no memory of the agent's work — it evaluates results independently.

### 10.9 Runs Are Persistent

Agent runs survive daemon restart. Server-side persistence with replay buffer. PID tracking for long-running tasks. Orphan detection and cleanup.

### 10.10 Agent Is the Central Nervous System

Everything serves the agent or is served by it. Memory feeds the agent. The graph feeds the agent. Retrieval serves the agent. Tools extend the agent. The agent is the primary consumer of the intelligence layer.

---

## 11. Development Principles

### 11.1 TDD Is Default

Write failing test → implement → verify pass → commit. Every new subsystem follows this cycle. 341 existing tests are the safety net.

### 11.2 Feature Flags for Risky Changes

Agent loop replacement, vector store abstraction, memory consolidation — all go behind feature flags. Old path + new path during transition. Gradual rollout.

### 11.3 Commit After Each Logical Unit

Small, focused commits. Each commit is self-contained and testable. `make lint` + `make format` after each commit.

### 11.4 Evidence-Based Decisions

Every architectural decision cites evidence from council deliverables. No opinion without data. No pattern without validation.

### 11.5 Governance Is Non-Negotiable

12 mandatory rules. 11 hooks. 10 workflows. 7 strategic commands. Reflection framework before completion. All followed, all the time.

### 11.6 Documentation Follows Code

When APIs change, docs update. When schemas change, docs update. When security patterns change, docs update. Documentation is never behind code.

### 11.7 One Phase at a Time

Phases are capability milestones, not calendar commitments. Each phase is complete when all deliverables are achieved. No rushing to the next phase.

### 11.8 Scope Is Guarded

Each subsystem gets its own spec → plan → implement cycle. Never implement more than 2 new subsystems simultaneously. Daily productivity tools are sequenced: foundation first, full tools later.

### 11.9 Tests Run Without Infrastructure

Backend tests use SQLite in-memory. No real PostgreSQL, Redis, or Qdrant needed. 13 blanket-mocked external services. Tests are fast and isolated.

### 11.10 Branching Is Mandatory

Feature branch before any significant change. Never commit directly to `main`. Branch naming: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`. Merge after verification.

---

## Appendix: Contradictions Resolved

This guide resolves the 17 contradictions identified in the council discovery phase:

| # | Contradiction | Resolution in Guide |
|---|--------------|---------------------|
| 1 | Two competing phase systems | Guide defines phases as capability milestones, not calendar commitments. Single numbering. |
| 2 | "Phase 2" means different things | Guide defines each domain's requirements independently. Phase alignment is implementation detail. |
| 3 | Agent system has no phase home | Agent rebuild is the central decision of Section 4.6. It has clear requirements. |
| 4 | "Local-first" vs Docker | Principle 3.1: Local-first. Section 4.2: Embedded by default, Docker for power. |
| 5 | "Daemon-first" vs web-first | Principle 3.3: Daemon-first. Section 4.1: Daemon architecture is the foundation. |
| 6 | "Autonomous agents" vs 5-tool prototype | Section 4.6: 30+ tools, streaming loop, compaction, security, persistence. |
| 7 | "CLI primary" vs stubs | Section 4.9: CLI is primary automation interface. 15 commands become real. |
| 8 | Tool approval dead code | Section 4.6: Per-turn tool policy replaces HMAC approval. Dead code eliminated. |
| 9 | SSRF bypass via exec_command | Section 4.6: Tool security is preserved and enhanced. |
| 10 | Command blocking bypass | Section 4.6: Broader pattern blocking. Allowlist approach where possible. |
| 11 | Embedding sync/async mismatch | Section 4.3: Service abstraction resolves this with clean interfaces. |
| 12 | Token estimation inaccuracy | Section 4.6: tiktoken for accurate counting. 10% safety margin. |
| 13 | Middleware directory missing | Resolved by documentation cleanup. Not an architectural concern. |
| 14 | Architecture diagram outdated | This guide IS the architecture. |
| 15 | "486+ tests" vs 341 actual | Guide references 341 as the verified count. |
| 16 | Priority vs dependency order | Guide separates requirements (what) from sequencing (when). |
| 17 | Daily tools DEFER→ADOPT | Section 4.7 + 4.8: Daily tools are part of the ecosystem architecture. |

---

## Appendix: What Cortex Keeps (From Current Implementation)

| Capability | Why It Stays |
|------------|-------------|
| PostgreSQL 16 | Best-in-class. Superior to all reference repos. |
| Two-password auth | Strong security model. Vault isolation. |
| Fernet vault encryption | Battle-tested. SecurePasswordCache. |
| Hybrid retrieval (RRF + MMR) | Best-in-class retrieval architecture. |
| Next.js 15 + React 19 frontend | Modern, well-supported. 21,800 lines of production code. |
| Three-tier embedding fallback | Graceful degradation. Becomes pluggable. |
| Arq background tasks | Becomes persistent job queue with persistence layer. |
| Docker Compose | Production-ready infrastructure. |
| TDD with SQLite in-memory | Fast, isolated, proven. |
| Multi-agent governance | Unmatched. Industry-leading. |
| "Warm Neural Dark" design | Distinctive, cohesive visual identity. |
| Code-aware knowledge graph | Unique capability. Universal expansion. |
| Incremental indexing | Unique capability. Code-aware chunking. |
| Confidence-based memory | Unique capability. Time-based decay. |
| Model management (3-source catalog) | Comprehensive. Hardware-aware. |
| All 341 tests | The safety net. Never reduce. |

---

**This document is the constitution of Cortex. Every implementation plan, every architectural decision, every feature prioritization must align with this guide. When in doubt, return to these principles.**
