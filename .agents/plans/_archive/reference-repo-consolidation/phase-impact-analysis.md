# Phase Impact Analysis

## Current Daemon-First Transition Plan (7 Phases)

The existing plan at `.agents/plans/2026-06-25-desktop-reorientation.md` covers infrastructure:
1. Daemon Foundation
2. Service Abstraction
3. Event Bus & Job System
4. CLI Completion
5. API Stabilization
6. Desktop Shell
7. Web UI Transition

## Three Parallel Workstreams (All 3 Batches)

The reference repo analysis identified critical gaps across three domains. These are ORTHOGONAL to the daemon transition and to each other. Each workstream has its own dependency chain.

### Workstream 1: Memory Intelligence (Batch 1)

**Depends on:** Phase 2 (Service Abstraction)
**Priority:** High — most impactful for Cortex's core value proposition

#### MI-1: Memory Consolidation Foundation
**Depends on:** Phase 2 (abstracted LLM + Vector Store)
**Entry criteria:** Service abstraction layer operational, LLM provider accessible
**Exit criteria:** Automated memory consolidation running, dedup working, contradiction detection active

**Scope:**
- M1: Memory Consolidation Pipeline (Mem0 + Graphiti + Cortex merge)
- A1: Memory Deduplication Pipeline (Mem0 V3 pattern)
- AD1: LLM-Based Entity Extraction (Graphiti pattern, adapted)
- AD5: Bi-Temporal Knowledge Tracking (Graphiti pattern, simplified)

**Key deliverables:**
```
backend/app/services/memory/
├── consolidation.py          # Two-phase extraction + consolidation
├── entity_extraction.py      # LLM-based entity extraction
├── deduplication.py          # 3-level dedup (batch, existing, hash)
├── contradiction_detector.py # Automatic contradiction detection
└── temporal.py               # Bi-temporal tracking (valid_at/invalid_at)
```

**New models/migrations:**
- Add `valid_at`, `invalid_at` to `LongTermMemory`
- Add `entity_source`, `linked_memory_ids`, `summary`, `labels` to `GraphNode`
- Add `memory_consolidation_log` table (audit trail)

#### MI-2: Search Intelligence
**Depends on:** MI-1 (needs entities and consolidated memories for entity boosting)
**Entry criteria:** MI-1 complete, entity extraction operational
**Exit criteria:** Adaptive scoring, entity boosting, MMR diversity all active

**Scope:**
- M2: Hybrid Search Pipeline merge (Mem0 + Graphiti + Cortex)
- A2: Triple-Signal Search Scoring (Mem0 pattern)
- A3: Query-Length-Adaptive BM25 Sigmoid (Mem0 pattern)
- AD2: Composable Search Recipes (Graphiti pattern, simplified)
- AD3: Entity Boosting During Search (Mem0 pattern, adapted)
- AD4: MMR Diversity Reranking (Graphiti pattern)
- R2: Score Normalization replacement (Mem0 adaptive formula)

**Key deliverables:**
```
backend/app/services/retrieval/
├── search_config.py          # Composable search recipes
├── score_fusion.py           # Adaptive score normalization
├── entity_boost.py           # Entity-based search boosting
├── rerankers/
│   ├── mmr.py                # Maximal Marginal Relevance
│   └── base.py               # Reranker protocol
└── hybrid_retrieval_v3.py    # Refactored pipeline
```

#### MI-3: Graph Intelligence
**Depends on:** MI-1 (needs entity extraction), MI-2 (needs search infrastructure)
**Entry criteria:** MI-1 and MI-2 complete
**Exit criteria:** LLM-based graph building, community detection, multi-hop traversal available

**Scope:**
- R1: Graph Builder → LLM-Based Extraction (replace regex)
- M3: Enhanced Entity Model (Mem0 + Graphiti + Cortex merge)
- D2: Community Detection (deferred from gap analysis — now unblocked)
- D4: Multi-Hop Graph Traversal (deferred — now unblocked with service abstraction)

**Key deliverables:**
```
backend/app/services/graph/
├── llm_graph_builder.py      # LLM-based entity + relationship extraction
├── community_detector.py     # Label propagation + LLM summaries
├── graph_traversal.py        # Multi-hop traversal (BFS/DFS)
└── entity_hydration.py       # Entity summary generation
```

---

### Workstream 2: Indexing Intelligence (Batch 2)

**Depends on:** Phase 2 (Service Abstraction)
**Priority:** High — directly impacts search quality and desktop viability

#### II-1: Indexing Pipeline Refactoring
**Depends on:** Phase 2 (service abstraction for vector store + embedding)
**Entry criteria:** Service abstraction layer operational
**Exit criteria:** Composable indexing pipeline, IngestionCache active, hierarchical chunking available

**Scope:**
- AD6: Hierarchical Chunking with Parent-Child (LlamaIndex pattern)
- AD7: Two-Phase Scan/Index Separation (sist2 pattern)
- A5: IngestionCache — Hash-Based Transform Caching (LlamaIndex pattern)

**Key deliverables:**
```
backend/app/services/indexing/
├── ingestion_cache.py        # Hash-based transform caching
├── scan_phase.py             # File scanning + change detection (mtime-based)
├── index_phase.py            # Chunking + embedding + upsert
└── chunker.py (modified)     # Add parent-child relationships
```

**New models/migrations:**
- Add `parent_chunk_id` to `DocumentChunk` (hierarchical linking)
- Add `ingestion_cache` table (hash → transform results)

#### II-2: Desktop-Ready Vector Storage
**Depends on:** Phase 6 (Desktop Shell)
**Entry criteria:** Desktop shell framework operational, turbovec binding available
**Exit criteria:** Quantized vectors available, Qdrant-free desktop mode works

**Scope:**
- AD12: Scalar Quantization for Desktop (turbovec pattern)
- R4: Vector Store → Abstracted Interface (AnythingLLM + LlamaIndex pattern)

**Key deliverables:**
```
backend/app/services/vector_db/
├── provider.py               # Vector store Protocol + registry
├── qdrant_provider.py        # Qdrant implementation (server mode)
├── quantized_store.py        # turbovec implementation (desktop mode)
└── sqlite_fts5.py            # FTS5 search (desktop mode, optional)
```

---

### Workstream 3: Platform Intelligence (Batch 3)

**Depends on:** Phase 2 (Service Abstraction)
**Priority:** Critical — enables extensibility, model routing, desktop mode

#### PI-1: Provider Abstraction & Plugin System
**Depends on:** Phase 2 (service abstraction)
**Entry criteria:** Service abstraction layer operational
**Exit criteria:** Formal provider Protocol, plugin registration, MCP integration

**Scope:**
- R3: Embedding Service → Pluggable Provider (replace hardcoded tiers)
- R4: Vector Store → Abstracted Interface (replace Qdrant-only)
- AD9: Plugin Architecture — 3-Layer Start (Open WebUI + AnythingLLM patterns)
- AD11: MCP Integration — Hypervisor Pattern (AnythingLLM pattern)

**Key deliverables:**
```
backend/app/core/
├── providers/
│   ├── __init__.py           # Provider registry
│   ├── protocol.py           # LLMProvider, EmbeddingProvider, VectorStore protocols
│   └── factory.py            # Provider factory + registration
backend/app/plugins/
├── __init__.py               # Plugin registry
├── base.py                   # Plugin Protocol definitions
├── registry.py               # Plugin discovery + loading
└── mcp/
    ├── hypervisor.py         # MCP client lifecycle management
    └── server.py             # MCP server (expose Cortex tools)
```

**New models/migrations:**
- Add `provider_config` JSON to vault settings (per-vault provider overrides)
- Add `mcp_servers` table (registered MCP server configs)

#### PI-2: Model Management & Settings
**Depends on:** PI-1 (needs provider abstraction for model routing)
**Entry criteria:** Provider abstraction operational
**Exit criteria:** Model routing active, PersistentConfig working, vault settings available

**Scope:**
- AD8: Model Routing (AnythingLLM pattern)
- AD10: Workspace/Vault Settings (AnythingLLM pattern)
- A7: PersistentConfig Pattern (Open WebUI pattern)
- A8: OpenAI-Compatible API (Open WebUI + AnythingLLM pattern)

**Key deliverables:**
```
backend/app/services/models/
├── model_router.py           # Rules-based routing per vault
├── context_window_finder.py  # Remote JSON + cache + fallback
backend/app/core/
├── persistent_config.py      # Env → DB → User config hierarchy
backend/app/api/v1/
├── openai_compat.py          # /v1/chat/completions, /v1/models, /v1/embeddings
```

**New models/migrations:**
- Add `model_routing_rules` table (per-vault routing config)
- Add `user_preferences` table (per-user settings)
- Add `system_settings` table (runtime-mutable config)

---

### Workstream 4: Agent Intelligence (Batch 4)

**Depends on:** Phase 2 (Service Abstraction), Phase 3 (Event Bus)
**Priority:** Critical — Cortex's agent system is the weakest subsystem across all batches

#### AI-1: Agent System Foundation
**Depends on:** Phase 2 (service abstraction for LLM providers + tool registry)
**Entry criteria:** Service abstraction layer operational
**Exit criteria:** Unified agent loop, decorator-based tools, context compaction, tool policy

**Scope:**
- R5: Agent System → Unified Agent Loop (replace Planner→Executor)
- R7: Tool Registry → Decorator-Based Registry (replace TOOL_REGISTRY dict)
- A9: @tool Decorator Pattern (Strands pattern)
- A10: Context Compaction (Continue + Odysseus pattern)
- A11: Tool Policy Composition (Continue + Odysseus pattern)
- AD16: Prompt Security Guards (Continue + Odysseus pattern)

**Key deliverables:**
```
backend/app/agents/
├── loop.py                    # Unified agent loop (replaces planner.py + executor.py)
├── policy.py                  # Tool policy composition (allow/deny/ask per context)
├── tools/
│   ├── __init__.py            # @tool decorator + auto-schema registry
│   ├── registry.py            # Tool discovery + validation + dynamic loading
│   ├── use_agent.py           # Multi-agent delegation tool
│   └── mcp_tool.py            # MCP tool wrapper
backend/app/services/context/
├── compaction.py              # Auto-compaction at 85% context window
├── security.py                # UNTRUSTED_SOURCE_DATA markers
└── providers/
    ├── __init__.py            # ContextProvider Protocol
    ├── codebase.py            # Codebase search provider
    ├── documents.py           # Document search provider
    ├── memory.py              # Memory search provider
    ├── graph.py               # Graph search provider
    └── vault.py               # Vault files provider
```

**New models/migrations:**
- Add `tool_spec` JSON column to `AgentTool` model
- Add `context_summary` column to `AgentRun` model (for compaction state)

#### AI-2: CLI & Daemon Management
**Depends on:** Phase 2 (service abstraction), Phase 3 (event bus + background jobs)
**Entry criteria:** Service abstraction and event bus operational
**Exit criteria:** Working CLI with daemon management, agent execution, knowledge operations

**Scope:**
- AD18: CLI Foundation (Continue + Odysseus pattern)
- AD12: Action Intent Classification (Odysseus pattern)
- AD15: Event Bus (Odysseus pattern)
- AD20: Agent Run Persistence (Odysseus pattern)

**Key deliverables:**
```
cli/src/
├── commands/
│   ├── daemon.ts              # daemon start/stop/status/logs
│   ├── agent.ts               # agent run/chat/list
│   ├── index.ts               # index run/status
│   ├── search.ts              # search "query"
│   ├── config.ts              # config set/get/list
│   └── vault.ts               # vault lock/unlock/status
├── prompts/
│   └── index.ts               # Ink TUI components (deferred to D15)
└── utils/
    ├── daemon.ts              # Daemon lifecycle management
    └── session.ts             # Session persistence
backend/app/services/events/
├── bus.py                     # Pub/sub event bus (Redis-backed)
└── scheduler.py               # Event-triggered task scheduling
backend/app/services/runner/
├── manager.py                 # Background agent run manager
└── persistence.py             # PID tracking + orphan detection + restart
```

**New models/migrations:**
- Add `pid` and `status` columns to `AgentRun` model (for daemon tracking)
- Add `event_log` table (audit trail for events)

#### AI-3: MCP & Multi-Agent Orchestration
**Depends on:** AI-1 (agent system foundation), PI-1 (provider abstraction + plugin system)
**Entry criteria:** Agent system operational, plugin system available
**Exit criteria:** MCP integration, multi-agent delegation, dynamic tool loading

**Scope:**
- A13: MCP Client Wrapper (Strands + Continue pattern)
- AD17: Multi-Agent Delegation (Strands use_agent pattern)
- AD19: Dynamic Tool Loading (Strands load_tool pattern)
- AD11: MCP Integration (AnythingLLM pattern, from PI-1)

**Key deliverables:**
```
backend/app/services/mcp/
├── client.py                  # MCP client (stdio + SSE transport)
├── hypervisor.py              # MCP server lifecycle (from PI-1)
├── server.py                  # MCP server (expose Cortex tools)
└── registry.py                # Registered MCP server configs
```

**New models/migrations:**
- Add `mcp_servers` table (registered MCP server configs) — shared with PI-1

---

### Unified Phase Dependencies Diagram

```
Daemon Workstream       Memory Intel    Indexing Intel   Platform Intel    Agent Intel
─────────────────       ────────────    ──────────────   ──────────────    ───────────
Phase 1: Daemon Foundation
    │
Phase 2: Service Abs ──→ MI-1: Memory  II-1: Indexing   PI-1: Providers   AI-1: Agent
    │                     Consolidation Pipeline Refactor & Plugins       System
    │                       │              │                │                │
Phase 3: Event Bus ───→ MI-2: Search    II-2: Desktop    PI-2: Model Mgmt AI-2: CLI &
    │                     Intel           Vector Storage  & Settings       Event Bus
    │                       │              │                │                │
Phase 4: CLI ─────────→ MI-3: Graph       │                │                │
    │                     Intel            │                │                │
Phase 5: API Stab ←──── All MI        ←── All II       ←── All PI      ←── AI-3: MCP
    │                                            │                │        & Multi-Agent
Phase 6: Desktop Shell                           │                │
    │                                            │                │
Phase 7: Web UI Transition                       │                │
```

### Resource Allocation Recommendation

| Workstream | Phases | Priority | can-parallelize? |
|------------|--------|----------|-------------------|
| Daemon | 1-7 | High | Sequential (each depends on previous) |
| Memory Intelligence | MI-1 to MI-3 | High | MI-1 must complete first; MI-2/MI-3 can partially overlap |
| Indexing Intelligence | II-1 to II-2 | High | II-1 after Phase 2; II-2 after Phase 6 |
| Platform Intelligence | PI-1 to PI-2 | Critical | PI-1 after Phase 2; PI-2 after PI-1 |
| Agent Intelligence | AI-1 to AI-3 | Critical | AI-1 after Phase 2; AI-2 after Phase 3; AI-3 after AI-1 + PI-1 |

**Recommendation:**
- Start **PI-1 (Providers + Plugins)** immediately after Phase 2 — this unblocks MI-1, AI-1, and II-1
- Start **AI-1 (Agent System Foundation)** in parallel with PI-1 — both need Phase 2, neither blocks the other
- Start **MI-1 (Memory Consolidation)** in parallel with PI-1 and AI-1 — all need Phase 2
- Start **II-1 (Indexing Pipeline)** after Phase 2 — can run in parallel with MI-1, PI-1, and AI-1
- Phase 2 is the critical bottleneck — all four workstreams depend on it
- **AI-1 is highest priority** among workstreams — Cortex's agent system is the weakest subsystem across all 4 batches

### Impact on Existing Phase Plan

The daemon-first transition plan does NOT need modification. The four intelligence workstreams are additive:

- **No changes to Phase 1-3:** Daemon foundation, service abstraction, event bus — these are prerequisites for all workstreams
- **No changes to Phase 4-5:** CLI and API — these benefit from intelligence improvements but don't depend on them
- **Phase 6-7 gains:** Desktop shell gets quantized vectors (II-2), plugin system (PI-1), model routing (PI-2)
- **Phase 5 gains:** API stabilization gets OpenAI-compatible API (PI-2), vault settings (PI-2)
- **Phase 4 gains:** CLI gets full implementation (AI-2), daemon management, agent execution commands
- **Phase 3 gains:** Event bus (AI-2), background agent run persistence (AI-2), MCP integration (AI-3)

### What NOT to Do

1. **Don't interleave workstream tasks into daemon phases.** Keep workstreams separate. Each has its own dependency chain.
2. **Don't start any workstream before Phase 2.** Service abstraction is a hard prerequisite for all four workstreams.
3. **Don't skip PI-1 and jump to PI-2.** Provider abstraction is the foundation for model routing, plugin system, and MCP integration.
4. **Don't skip MI-1 and jump to MI-2/MI-3.** Consolidation is the foundation. Search and graph intelligence need consolidated memories to be useful.
5. **Don't implement all recommendations at once.** Follow the priority order in recommendations.md.
6. **Don't start II-2 (Desktop Vector Storage) before Phase 6.** Desktop shell is the prerequisite for desktop-specific optimizations.
7. **Don't start D8 (Community Marketplace) before AD9 (Plugin Architecture).** Marketplace needs plugins to exist first.
8. **Don't skip AI-1 and jump to AI-2/AI-3.** Agent system foundation (loop, tools, compaction) is prerequisite for CLI and MCP.
9. **Don't implement swarm/workflow DAG before basic agent delegation.** Start with simple use_agent, add complexity later (D13, D14).
10. **Don't add Ink TUI before headless CLI works.** Start with Commander.js output, add TUI later (D15).

### Conflict Resolution Between Batches

| Conflict | Batch 1 | Batch 2/3 | Resolution |
|----------|---------|-----------|------------|
| **SQLite vs PostgreSQL** | REJECT SQLite for history (X1) | sist2 uses SQLite FTS5; AnythingLLM uses SQLite+Prisma | Keep PostgreSQL for platform data. SQLite ONLY for desktop-mode vector storage (turbovec) and optional FTS5 search. |
| **Vector store abstraction** | Mem0: 24 swappable backends | AnythingLLM: 10 vector DBs; LlamaIndex: 70+ backends | MERGE: Create Protocol-based abstraction with Qdrant (server) and turbovec (desktop) as first implementations. |
| **Provider count** | Mem0: 18 providers; Graphiti: 4 drivers | AnythingLLM: 35 LLM + 15 embedding + 10 vector | REJECT 35+ providers (X7). Focus on 4-5 key providers via Protocol. Community can add more. |
| **Embedding tiers** | Mem0: configurable per provider | Cortex: hardcoded ONNX→Ollama→Mock | REPLACE with pluggable provider (R3). Keep ONNX as default for desktop. |
| **Search scoring** | Mem0: triple-signal adaptive | LlamaIndex: 7 response modes; sist2: FTS5 BM25 | MERGE: Keep Cortex's three sources. Add adaptive normalization (Mem0). Add response synthesis modes (LlamaIndex) as future enhancement. |
| **Agent model** | Cortex: Planner→Executor two-agent | Continue: single tool-calling loop. Strands: tool loop with hooks. Odysseus: multi-turn with action intents | REPLACE with unified agent loop (R5). Planner concept becomes a planning tool, not a separate agent. |
| **Tool definition** | Cortex: hand-maintained TOOL_REGISTRY dict | Strands: @tool decorator auto-schema. Continue: Tool type with policy hooks. Odysseus: 30+ tools with XML/FC/MD parsing | REPLACE with @tool decorator (R7) + policy hooks (A11). Function-calling format only (reject XML/MD). |
| **Tool invocation** | Cortex: HMAC approval tokens for 3 tools | Continue: per-tool ToolPolicy allow/deny/ask. Odysseus: per-turn policy composition | ADOPT policy composition (A11). HMAC tokens insufficient for nuanced permissions. |
| **Context management** | Cortex: no compaction, simple truncation | Continue: auto at 85%. Odysseus: auto at 85% with structured summary | ADOPT structured compaction (A10). Cortex is only repo without any compaction. |
| **Multi-agent** | Cortex: planner→executor (2 agents) | Strands: use_agent, swarm (N agents), workflow (DAG). Odysseus: single agent with action intents | ADAPT simple delegation (AD17) first. Defer swarm (D13) and workflow DAG (D14). |
| **MCP integration** | Cortex: none | Continue: MCPManagerSingleton. Strands: MCPTool wrapper. Odysseus: McpManager | ADOPT MCP client wrapper (A13). All 3 repos have MCP — it's table stakes. |
| **CLI** | Cortex: 15 stubs, zero functionality | Continue: Commander.js + Ink TUI. Odysseus: 20+ specialized CLIs | ADAPT Continue's dual-mode pattern (AD18). Start with headless, defer Ink TUI (D15). |
