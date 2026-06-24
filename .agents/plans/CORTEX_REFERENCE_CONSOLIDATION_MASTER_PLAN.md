# CORTEX Reference Repository Consolidation — Master Plan

> **This document is the permanent knowledge transfer from 10 reference repositories before `docs/ref/` is deleted.**
>
> Date: 2026-06-25
> Author: Architecture Review Board (consolidated from 4 batches + Odysseus deep audit)
> Scope: All findings from Mem0, Graphiti, LlamaIndex, sist2, turbovec, Open WebUI, AnythingLLM, ollama-catalog, Continue, Odysseus, Strands Tools

---

## 1. Executive Summary

CORTEX analyzed 10 reference repositories across 4 batches to identify every valuable pattern, capability, and abstraction that can be absorbed into Cortex's architecture. The analysis produced:

| Metric | Count |
|--------|-------|
| **Gaps identified** | 73 (19 critical, 30 important, 18 nice-to-have, 6 architecture) |
| **Recommendations** | 72 (13 ADOPT, 20 ADAPT, 3 MERGE, 7 REPLACE, 17 DEFER, 12 REJECT) |
| **Odysseus integration items** | 24 (15,000+ lines to harvest) |
| **Action items** | 15 implementation work items across 4 workstreams |
| **Total source analyzed** | ~200,000+ lines across 10 repositories |

### Key Finding

Cortex has **superior infrastructure** (PostgreSQL, Next.js, Qdrant, Redis, knowledge graph, hybrid RAG, 486+ tests, governance) but a **broken agent system** and **zero daily productivity tools**. The reference repos — especially Odysseus — have working agent intelligence and a complete AI assistant layer on inferior infrastructure.

**The path forward:** Keep Cortex's infrastructure. Absorb Odysseus's agent intelligence (streaming loop, 30+ tools, compaction, security). Absorb Odysseus's daily productivity layer (email, calendar, tasks, notes, documents, contacts, research, skills, webhooks). Absorb memory/INDEXING/platform patterns from Batches 1-3.

**Result:** An AI workspace that is both *intelligent* (Odysseus agent patterns), *productive* (Odysseus daily tools), and *robust* (Cortex infrastructure).

---

## 2. Architecture Recommendations

### 2.1 Agent System — COMPLETE REBUILD (R5, AD13, R7)

| Aspect | Cortex Current | Target State | Source |
|--------|---------------|--------------|--------|
| Architecture | Planner→Executor (2 agents) | Single streaming agent loop | Odysseus (3,485-line async generator) |
| Tool calling | Max 10 iterations, no abort | Max 25 rounds, stall detection, force-answer | Odysseus |
| Tool selection | All tools in prompt | RAG-based retrieval (when 15+ tools) | Odysseus ChromaDB-backed |
| Tool count | 5 tools, no schemas | 30+ tools with full JSON Schema | Odysseus + Strands |
| Tool definition | Hand-maintained TOOL_REGISTRY | @tool decorator with auto-schema | Strands |
| Tool policy | HMAC approval tokens | Per-turn composition (allow/deny/ask) | Odysseus + Continue |
| Context management | Simple truncation | Auto-compaction at 85% with structured summary | Odysseus |
| Prompt security | None | UNTRUSTED_SOURCE_DATA guards | Odysseus + Continue |
| Completion detection | None | Fresh-context LLM verifier subagent | Odysseus |
| Detached execution | asyncio tasks (lost on restart) | Server-side runs with replay buffer | Odysseus |
| Intent classification | None | casual/admin/agent/continuation routing | Odysseus |
| Loop-breaking | Hard cutoff at 10 | Stall detection + force-answer | Odysseus |
| Low-signal detection | None | Casual messages → fast path | Odysseus |

**Classification:** REPLACE (R5, R7) + ADAPT (AD13)
**Impact:** Critical — single most impactful change
**Complexity:** High — core system rewrite (estimated 2-3 days)
**Dependencies:** Phase 2 (Service Abstraction) for provider interfaces
**Risks:** Agent loop is Cortex's central nervous system; breakage cascades everywhere
**Suggested Phase:** Phase 2-3

### 2.2 Tool System — Decorator-Based Registry (R7, A9)

| Aspect | Cortex Current | Target State | Source |
|--------|---------------|--------------|--------|
| Tool count | 5 | 30+ | Odysseus + Strands + Continue |
| Tool schemas | No parameter schemas | Full OpenAI-compatible JSON Schema | Odysseus (60+ schemas) |
| Tool definition | TOOL_REGISTRY dict | @tool decorator + auto-schema from type hints | Strands |
| Tool policy | HMAC approval | Per-turn composition | Odysseus + Continue |
| Tool security | Workspace restriction | Path confinement + SSRF + sensitive path blocking | Odysseus |
| Dynamic loading | None | Load from ~/.cortex/tools/ + MCP | Strands + MCP |

**Classification:** REPLACE (R7) + ADOPT (A9)
**Impact:** Critical — foundation for all tool improvements
**Complexity:** Medium — replaces existing tools.py
**Dependencies:** None (can start immediately)
**Risks:** Low — additive changes, old tools can be wrapped
**Suggested Phase:** Phase 2

### 2.3 Context Architecture — Compaction + Security + Providers (A10, AD14, AD16)

| Aspect | Cortex Current | Target State | Source |
|--------|---------------|--------------|--------|
| Compaction | None (truncation) | Auto at 85% with Goal/Done/State/Pending summary | Odysseus |
| Security | None on external content | UNTRUSTED_SOURCE_DATA markers on all external data | Odysseus + Continue |
| Providers | Monolithic RAG pipeline | Composable IContextProvider pattern | Continue (20+ providers) |
| Domain rules | Static prompt for all tasks | Tool-to-domain mapping per task type | Odysseus |
| Skill injection | Dev-time only | Runtime Jaccard-matched skill injection | Odysseus |

**Classification:** ADOPT (A10) + ADAPT (AD14, AD16)
**Impact:** Critical — enables long conversations without context loss
**Complexity:** Medium — prompt engineering + provider pattern refactor
**Dependencies:** Phase 2 (needs LLM provider for compaction calls)
**Risks:** Medium — compaction quality affects agent performance
**Suggested Phase:** Phase 2-3

### 2.4 MCP Integration (AD11, A13)

| Aspect | Cortex Current | Target State | Source |
|--------|---------------|--------------|--------|
| MCP client | None | Full MCP manager (stdio + SSE, lifecycle) | Odysseus + Continue |
| MCP server | None | Expose Cortex tools to other MCP clients | AnythingLLM hypervisor |
| Tool wrapping | None | MCPTool wrapper for external MCP tools | Strands |

**Classification:** ADAPT (AD11, A13)
**Impact:** Critical — MCP is table stakes for agent interoperability
**Complexity:** High — protocol implementation + lifecycle management
**Dependencies:** Phase 3 (event bus for async message handling)
**Risks:** Medium — MCP ecosystem is still evolving
**Suggested Phase:** Phase 3

### 2.5 Plugin Architecture — 3-Layer Start (AD9)

| Layer | Purpose | Source |
|-------|---------|--------|
| Layer 1: Providers | LLM, embedding, vector store (Protocol interfaces) | Open WebUI + AnythingLLM |
| Layer 2: Tools | Function-calling tools (MCP-compatible) | Open WebUI + Strands |
| Layer 3: Pipelines | Processing chains (indexing, consolidation, retrieval) | LlamaIndex composable RAG |

**Classification:** ADAPT (AD9)
**Impact:** Critical — enables extensibility without forking
**Complexity:** High — new subsystem + provider refactoring
**Dependencies:** Phase 2 (service abstraction)
**Risks:** Medium — plugin interface stability matters
**Suggested Phase:** Phase 2-3

---

## 3. Memory Recommendations

### 3.1 Memory Consolidation Pipeline (M1)

**Classification:** MERGE (Mem0 + Graphiti + Cortex)
**Impact:** Critical — the single most impactful memory improvement
**Complexity:** High — new subsystem
**Dependencies:** Phase 2 (abstracted LLM provider)
**Risks:** High — consolidation quality directly affects memory reliability
**Suggested Phase:** Parallel to Phase 2-3

Combine three approaches:
1. **Mem0:** Two-phase extraction (ADD-only extraction + consolidation)
2. **Graphiti:** Automatic contradiction detection + invalidation
3. **Cortex:** Confidence scoring + time-based decay

Result: Extract new facts → compare against existing (dedup + contradiction) → assign confidence → invalidate contradictions → apply decay.

### 3.2 Memory Deduplication (A1)

**Classification:** ADOPT (Mem0 V3 pattern)
**Impact:** Important — prevents memory duplication
**Complexity:** Medium
**Dependencies:** M1 (consolidation pipeline)
**Risks:** Low — additive
**Suggested Phase:** Parallel to Phase 2-3

Mem0 V3 3-level dedup: (1) batch-level dedup within extraction, (2) existing-memory dedup via vector similarity, (3) hash-based exact match.

### 3.3 LLM-Based Entity Extraction (AD1)

**Classification:** ADAPT (Graphiti pattern)
**Impact:** Important — replaces regex-based extraction
**Complexity:** Medium
**Dependencies:** Phase 2 (LLM provider)
**Risks:** Medium — LLM extraction quality varies
**Suggested Phase:** Parallel to Phase 2-3

### 3.4 Bi-Temporal Knowledge Tracking (AD5)

**Classification:** ADAPT (Graphiti pattern, simplified)
**Impact:** Important — enables temporal queries
**Complexity:** Low — schema change + prompt update
**Dependencies:** M1
**Risks:** Low
**Suggested Phase:** After M1

Add `valid_at` / `invalid_at` to `LongTermMemory`. Keep existing `created_at` / `updated_at`.

---

## 4. Knowledge Graph Recommendations

### 4.1 LLM-Based Graph Builder (R1)

**Classification:** REPLACE (Graphiti LLM extraction)
**Impact:** Critical — current regex extraction is too brittle
**Complexity:** High — new subsystem + prompt engineering
**Dependencies:** Phase 2 (LLM provider)
**Risks:** High — graph quality affects all downstream graph queries
**Suggested Phase:** After M1

Replace regex-based edge extraction with LLM-based entity + relationship extraction.

### 4.2 Enhanced Entity Model (M3)

**Classification:** MERGE (Mem0 + Graphiti + Cortex)
**Impact:** Important — richer entity model
**Complexity:** Medium
**Dependencies:** M1
**Risks:** Low
**Suggested Phase:** After M1

Enhanced GraphNode with: `entity_source`, `linked_memory_ids`, `summary`, `labels`.

### 4.3 Community Detection (D2)

**Classification:** DEFER
**Impact:** Nice-to-have
**Rationale:** Requires richer entity graph first
**Suggested Phase:** After M3

### 4.4 Multi-Hop Graph Traversal (D4, D12)

**Classification:** DEFER
**Impact:** Nice-to-have
**Rationale:** Requires graph DB optimization
**Suggested Phase:** Phase 2-3

---

## 5. Retrieval Recommendations

### 5.1 Hybrid Search Pipeline (M2)

**Classification:** MERGE (Mem0 + Graphiti + Cortex)
**Impact:** Critical — search quality improvement
**Complexity:** High — major refactor
**Dependencies:** M1 (needs consolidated memories for entity boosting)
**Risks:** High — search quality is user-visible
**Suggested Phase:** After M1

Combine: Cortex three-source base + Mem0 adaptive normalization + Mem0 entity boosting + Graphiti MMR diversity.

### 5.2 Adaptive Score Normalization (R2)

**Classification:** REPLACE (Mem0 adaptive formula)
**Impact:** Important
**Complexity:** Low
**Dependencies:** M2
**Risks:** Low
**Suggested Phase:** After M2

### 5.3 Composable Search Recipes (AD2)

**Classification:** ADAPT (Graphiti pattern)
**Impact:** Important
**Complexity:** Medium
**Dependencies:** M2
**Risks:** Low
**Suggested Phase:** After M2

### 5.4 Entity Boosting (AD3)

**Classification:** ADAPT (Mem0 pattern)
**Impact:** Important
**Complexity:** Medium
**Dependencies:** M1 + M2
**Risks:** Low
**Suggested Phase:** After M2

### 5.5 MMR Diversity Reranking (AD4)

**Classification:** ADAPT (Graphiti pattern)
**Impact:** Important
**Complexity:** Low
**Dependencies:** M2
**Risks:** Low
**Suggested Phase:** After M2

### 5.6 Cross-Encoder Reranking (D1)

**Classification:** DEFER
**Rationale:** Requires GPU or API dependency
**Suggested Phase:** Phase 6-7

---

## 6. Agent Recommendations (Daily Productivity Tools)

> **Note:** User explicitly required ALL daily productivity tools to be included. None are deferred.

### 6.1 Task Scheduler (Tier 3 — Phase 4+)

| Aspect | Source | Complexity | Lines |
|--------|--------|------------|-------|
| Cron/event/webhook triggers | Odysseus task_scheduler.py | Medium | 2,467 |
| 10 built-in housekeeping tasks | Odysseus | Medium | — |
| Personal assistant CrewMember | Odysseus | High | — |
| Note pings (60s interval scanner) | Odysseus | Medium | — |

**Classification:** ADOPT
**Impact:** Critical — enables autonomous operation
**Complexity:** High
**Dependencies:** Agent loop (AD13), event bus (AD15)
**Risks:** Medium — scheduling reliability
**Suggested Phase:** Phase 4

### 6.2 Skills System (Tier 3 — Phase 4+)

| Aspect | Source | Complexity | Lines |
|--------|--------|------------|-------|
| Disk-based SKILL.md with YAML frontmatter | Odysseus skills.py | Low | 2,370 |
| Slash-command invocation | Odysseus | Medium | — |
| Autonomous audit (self-edit → retry → teacher → flag) | Odysseus | High | — |
| Usage tracking (sidecar _usage.json) | Odysseus | Low | — |
| Duplicate detection | Odysseus | Medium | — |

**Classification:** ADOPT
**Impact:** High — extensible skill system
**Complexity:** High
**Dependencies:** Agent loop
**Risks:** Low
**Suggested Phase:** Phase 4

### 6.3 Webhooks (Tier 3 — Phase 4+)

| Aspect | Source | Complexity | Lines |
|--------|--------|------------|-------|
| CRUD + test | Odysseus webhook_routes.py | Low | 395 |
| API token sync (n8n/Make/Activepieces) | Odysseus | Medium | — |
| Provider auto-detection | Odysseus | Low | — |

**Classification:** ADAPT
**Impact:** Medium
**Complexity:** Medium
**Dependencies:** Event bus
**Risks:** Low
**Suggested Phase:** Phase 4

### 6.4 Agent-to-Agent Sessions (Tier 3 — Phase 4+)

| Aspect | Source | Complexity | Lines |
|--------|--------|------------|-------|
| Create/send/list/manage sessions | Odysseus session_tools.py | Medium | 465 |
| Named sessions with model selection | Odysseus | Low | — |
| Archive, rename, fork, truncate | Odysseus | Low | — |

**Classification:** ADOPT
**Impact:** Medium
**Complexity:** Medium
**Dependencies:** Agent loop, model routing
**Risks:** Low
**Suggested Phase:** Phase 4

### 6.5 Teacher Escalation (Tier 3 — Phase 4+)

| Aspect | Source | Complexity | Lines |
|--------|--------|------------|-------|
| LLM-to-LLM consultation (ask_teacher) | Odysseus | Low | — |

**Classification:** ADOPT
**Impact:** Low — novel but niche
**Complexity:** Low
**Dependencies:** LLM provider
**Risks:** Low
**Suggested Phase:** Phase 4

### 6.6 RAG-based Tool Selection (Tier 3 — Phase 4+)

| Aspect | Source | Complexity | Lines |
|--------|--------|------------|-------|
| ChromaDB-backed tool description embedding | Odysseus tool_index.py | High | — |
| Top-K relevant tools per user message | Odysseus | Medium | — |

**Classification:** ADAPT
**Impact:** Medium — only needed when 15+ tools
**Complexity:** High
**Dependencies:** Embeddings, tool system
**Risks:** Medium — retrieval quality affects agent performance
**Suggested Phase:** Phase 4 (when tool count exceeds 15)

### 6.7 Domain-specific Rules

| Aspect | Source | Complexity | Lines |
|--------|--------|------------|-------|
| Tool-to-domain mapping | Odysseus | Medium | — |
| Domain-specific rule injection | Odysseus | Medium | — |

**Classification:** ADAPT
**Impact:** Medium
**Complexity:** Medium
**Dependencies:** Context providers
**Risks:** Low
**Suggested Phase:** Phase 4

---

## 7. Desktop Recommendations

### 7.1 Vector Store Abstraction (R4)

**Classification:** REPLACE (Qdrant-only → abstracted interface)
**Impact:** Critical — enables desktop mode without Qdrant
**Complexity:** High — new abstraction + multiple backends
**Dependencies:** Phase 2 (service abstraction)
**Risks:** High — vector store is central to search
**Suggested Phase:** Phase 2 (abstraction) + Phase 6 (desktop implementation)

### 7.2 Scalar Quantization for Desktop (AD12)

**Classification:** ADAPT (turbovec pattern)
**Impact:** Important — enables desktop deployment without Qdrant
**Complexity:** High — Rust extension or Python binding
**Dependencies:** R4 (vector store abstraction)
**Risks:** Medium — quantization affects recall
**Suggested Phase:** Phase 6

### 7.3 PersistentConfig Pattern (A7)

**Classification:** ADOPT (Open WebUI pattern)
**Impact:** Important — Env → DB → User config hierarchy
**Complexity:** Medium
**Dependencies:** Phase 2
**Risks:** Low
**Suggested Phase:** Phase 2 or 5

### 7.4 Model Routing (AD8)

**Classification:** ADAPT (AnythingLLM pattern)
**Impact:** Critical — daemon uses right model for right task
**Complexity:** Medium
**Dependencies:** Provider abstraction (Phase 2)
**Risks:** Medium — routing rules need tuning
**Suggested Phase:** After Phase 2

### 7.5 Vault Settings (AD10)

**Classification:** ADAPT (AnythingLLM pattern)
**Impact:** Important — per-project customization
**Complexity:** Medium
**Dependencies:** Phase 5 (API stabilization)
**Risks:** Low
**Suggested Phase:** Phase 5

### 7.6 Desktop Shell (Phase 6)

Cortex's Tauri-based desktop shell supersedes Odysseus's PyInstaller portable. Keep the Tauri plan.

---

## 8. CLI Recommendations

### 8.1 CLI Foundation (AD18)

**Classification:** ADAPT (Continue + Odysseus patterns)
**Impact:** Critical — no CLI means no daemon management
**Complexity:** High — many commands, but incremental
**Dependencies:** Phase 3 (event bus)
**Risks:** Medium — CLI UX matters for adoption
**Suggested Phase:** Phase 4

Commands to implement:
- `cortex daemon start/stop/status/logs`
- `cortex agent run/chat/list`
- `cortex index run/status`
- `cortex search "query"`
- `cortex config set/get/list`
- `cortex vault lock/unlock/status`

### 8.2 Ink TUI (D15)

**Classification:** DEFER
**Rationale:** Start with headless Commander.js, add TUI later
**Suggested Phase:** After AD18 headless CLI

---

## 9. Daemon Recommendations

### 9.1 Event Bus (AD15)

**Classification:** ADAPT (Odysseus pattern)
**Impact:** High — enables daemon mode, decoupled services
**Complexity:** Medium
**Dependencies:** Phase 3
**Risks:** Medium — event ordering and delivery guarantees
**Suggested Phase:** Phase 3

### 9.2 Detached Agent Runs (Odysseus)

**Classification:** ADOPT
**Impact:** Critical — daemon mode requires persistent runs
**Complexity:** Medium
**Dependencies:** Event bus (AD15)
**Risks:** Medium — replay buffer complexity
**Suggested Phase:** Phase 3

### 9.3 Agent Run Persistence (AD20)

**Classification:** ADAPT (Odysseus pattern)
**Impact:** High — reliable daemon-mode agent execution
**Complexity:** Medium
**Dependencies:** Agent loop (AD13)
**Risks:** Low
**Suggested Phase:** Phase 3

### 9.4 Background Tasks → Event-Driven Runner (R6)

**Classification:** REPLACE (asyncio tasks → persistent runner)
**Impact:** High — daemon mode requires reliable background execution
**Complexity:** High
**Dependencies:** Event bus, agent loop
**Risks:** High — replaces existing background.py
**Suggested Phase:** Phase 3

### 9.5 OpenAI-Compatible API (A8)

**Classification:** ADOPT (Open WebUI + AnythingLLM)
**Impact:** Important — enables external tool integration
**Complexity:** Medium
**Dependencies:** Provider abstraction
**Risks:** Low
**Suggested Phase:** Phase 5

---

## 10. Refactoring Recommendations

### 10.1 Files to Refactor

| Current File | Target | Reason |
|-------------|--------|--------|
| `backend/app/agents/tools.py` | `backend/app/agents/tools/` package | Split into registry, schemas, policy, security |
| `backend/app/agents/executor.py` | `backend/app/agents/loop.py` | Unified streaming loop |
| `backend/app/agents/planner.py` | Deprecate (planner becomes a tool) | Not a separate agent |
| `backend/app/agents/background.py` | `backend/app/services/runner/` package | Manager + persistence + replay |
| `backend/app/services/embedding/service.py` | `backend/app/services/embedding/provider.py` + registry | Pluggable provider |
| `backend/app/services/vector_db/qdrant_client.py` | `backend/app/services/vector_db/provider.py` + registry | Abstracted interface |
| `backend/app/services/rag_pipeline.py` | `backend/app/services/context/providers/` | Composable context providers |

### 10.2 New Packages to Create

| Package | Purpose | Source Pattern |
|---------|---------|---------------|
| `backend/app/agents/tools/` | Tool registry, schemas, policy, security | Odysseus + Strands |
| `backend/app/agents/policy.py` | Per-turn tool policy composition | Odysseus + Continue |
| `backend/app/services/context/` | Compactor, security, budget, domain rules | Odysseus + Continue |
| `backend/app/services/context/providers/` | Composable context sources | Continue |
| `backend/app/services/runner/` | Agent run manager, persistence, replay | Odysseus |
| `backend/app/services/events/` | Event bus, task scheduler | Odysseus |
| `backend/app/services/mcp/` | MCP client, hypervisor, server | Odysseus + AnythingLLM |
| `backend/app/services/tools/` | Tool index (RAG-based selection) | Odysseus |
| `backend/app/services/intent/` | Intent classifier | Odysseus |
| `backend/app/services/skills/` | Runtime skill injection | Odysseus |
| `backend/app/services/sessions/` | Session search | Odysseus |
| `backend/app/services/email/` | IMAP/SMTP, parser, triage, reply | Odysseus |
| `backend/app/services/calendar/` | CRUD, ICS, CalDAV, RRULE, parser | Odysseus |
| `backend/app/services/notes/` | Notes, checklists, reminders | Odysseus |
| `backend/app/services/documents/` | Living docs, PDF, AI tidy | Odysseus |
| `backend/app/services/contacts/` | CardDAV, resolution | Odysseus |
| `backend/app/services/research/` | Multi-step web research | Odysseus |
| `backend/app/services/scheduler/` | Task scheduler, housekeeping | Odysseus |
| `backend/app/services/webhooks/` | Webhook CRUD + test | Odysseus |
| `backend/app/core/providers/` | Provider protocols + factory | Open WebUI + AnythingLLM |
| `backend/app/plugins/` | Plugin base, registry | Open WebUI + AnythingLLM |

### 10.3 New Models to Create

| Model | Purpose | Source |
|-------|---------|--------|
| `ScheduledTask` | Cron/event/webhook triggers, run history | Odysseus |
| `EmailAccount` | IMAP/SMTP account config | Odysseus |
| `EmailMessage` | Email storage + metadata | Odysseus |
| `EmailTag` | Email tags + triage | Odysseus |
| `Calendar` | Calendar accounts | Odysseus |
| `CalendarEvent` | Events with RRULE | Odysseus |
| `Note` | Notes/checklists with reminders | Odysseus |
| `Document` | Living documents with version history | Odysseus |
| `DocumentVersion` | Version tracking | Odysseus |
| `Contact` | CardDAV contacts | Odysseus |
| `Webhook` | Outgoing webhooks | Odysseus |
| `MCPServer` | Registered MCP server configs | Odysseus + AnythingLLM |

### 10.4 Migrations to Create

| Migration | Purpose |
|-----------|---------|
| Add `valid_at`, `invalid_at` to LongTermMemory | Bi-temporal knowledge (AD5) |
| Add `entity_source`, `linked_memory_ids`, `summary`, `labels` to GraphNode | Enhanced entity model (M3) |
| Add `parent_chunk_id` to DocumentChunk | Hierarchical chunking (AD6) |
| Add `ingestion_cache` table | Hash-based transform caching (A5) |
| Add `tool_spec` JSON to AgentTool | Tool schemas (A9) |
| Add `context_summary` to AgentRun | Compaction state (A10) |
| Add `pid`, `status` to AgentRun | Daemon tracking (AD20) |
| Add `provider_config` JSON to vault settings | Per-vault provider overrides (AD10) |
| Add `model_routing_rules` table | Model routing (AD8) |
| Add `user_preferences` table | Per-user settings (A7) |
| Add `system_settings` table | Runtime-mutable config (A7) |
| Add `event_log` table | Event audit trail (AD15) |
| Add all daily productivity tables | Email, calendar, notes, documents, contacts, tasks, webhooks |

---

## 11. Immediate Adoption Candidates

These can be implemented in under 4 hours each with high impact:

| # | Item | Effort | Impact | Source | How |
|---|------|--------|--------|--------|-----|
| 1 | Add JSON Schema to 5 existing tools | 1h | High | Odysseus tool_schemas.py | Copy pattern |
| 2 | Add SSRF protection to web_fetch | 30m | High | Odysseus _is_private_url | Copy function |
| 3 | Add path confinement to file tools | 30m | High | Odysseus _resolve_tool_path | Copy function |
| 4 | Add UNTRUSTED_SOURCE_DATA to RAG results | 1h | High | Odysseus prompt_security.py | Copy pattern |
| 5 | Add intent classification (casual detection) | 2h | High | Odysseus _classify_agent_request | Copy pattern |
| 6 | Add context compaction | 4h | Critical | Odysseus context_compactor.py | Adapt |
| 7 | Add ToolPolicy dataclass | 1h | High | Odysseus tool_policy.py | Copy |
| 8 | Add loop-breaker | 1h | High | Odysseus _detect_runaway_call | Copy function |

---

## 12. Strategic Backlog

### Tier 1: Phase 2 — Service Abstraction (Critical Path)

| # | Item | Classification | Effort | Impact |
|---|------|---------------|--------|--------|
| 1 | Provider abstraction (LLM, embedding, vector store) | REPLACE (R3, R4) | High | Critical |
| 2 | Tool system rebuild (schemas + policy + security) | REPLACE (R7) + ADOPT (A9) | Medium | Critical |
| 3 | Agent loop rebuild (streaming + intent + low-signal) | REPLACE (R5) + ADAPT (AD13) | High | Critical |
| 4 | Context compaction (auto at 85%) | ADOPT (A10) | Low | Critical |
| 5 | Prompt security (UNTRUSTED_SOURCE_DATA) | ADAPT (AD16) | Low | Critical |
| 6 | Tool policy composition | ADOPT (A11) | Low | High |
| 7 | Plugin architecture (3 layers) | ADAPT (AD9) | High | Critical |
| 8 | PersistentConfig pattern | ADOPT (A7) | Medium | Important |

### Tier 2: Phase 3 — Event Bus & Jobs

| # | Item | Classification | Effort | Impact |
|---|------|---------------|--------|--------|
| 9 | Event bus (Redis-backed pub/sub) | ADAPT (AD15) | Medium | High |
| 10 | Detached agent runs (server-side + replay) | ADOPT | Medium | Critical |
| 11 | Agent run persistence (PID tracking + orphan detection) | ADAPT (AD20) | Medium | High |
| 12 | Background tasks → event-driven runner | REPLACE (R6) | High | High |
| 13 | Loop-breaker (stall detection) | ADOPT | Low | High |
| 14 | Completion verifier (fresh-context subagent) | ADOPT | Medium | High |
| 15 | Session search | ADOPT | Medium | Medium |
| 16 | Runtime skill injection | ADOPT | Medium | Medium |
| 17 | Context provider architecture | ADAPT (AD14) | Medium | High |
| 18 | MCP integration | ADAPT (AD11, A13) | High | Critical |
| 19 | Intent classification | ADOPT (A12) | Low | Medium |

### Tier 3: Phase 4 — CLI & Daily Tools Foundation

| # | Item | Classification | Effort | Impact |
|---|------|---------------|--------|--------|
| 20 | CLI foundation (headless commands) | ADAPT (AD18) | High | Critical |
| 21 | Task scheduler (cron/event/webhook, housekeeping) | ADOPT | High | Critical |
| 22 | Skills system (runtime, slash-commands, audit) | ADOPT | High | High |
| 23 | Webhooks (CRUD + API token sync) | ADAPT | Medium | Medium |
| 24 | Agent-to-agent sessions | ADOPT | Medium | Medium |
| 25 | Teacher escalation | ADOPT | Low | Low |
| 26 | RAG-based tool selection (when 15+ tools) | ADAPT | High | Medium |
| 27 | Domain-specific rules | ADAPT | Medium | Medium |
| 28 | Model routing | ADAPT (AD8) | Medium | Critical |
| 29 | Dynamic tool loading | ADAPT (AD19) | Medium | Medium |
| 30 | Memory consolidation pipeline | MERGE (M1) | High | Critical |
| 31 | Memory dedup pipeline | ADOPT (A1) | Medium | Important |
| 32 | LLM-based entity extraction | ADAPT (AD1) | Medium | Important |
| 33 | Two-phase scan/index separation | ADAPT (AD7) | Medium | Important |
| 34 | IngestionCache | ADOPT (A5) | Medium | Important |
| 35 | Hierarchical chunking | ADAPT (AD6) | Medium | Critical |

### Tier 4: Phase 5+ — Full AI Assistant

| # | Item | Classification | Effort | Impact |
|---|------|---------------|--------|--------|
| 36 | Deep research engine | ADOPT | High | High |
| 37 | Email system (IMAP/SMTP, triage, AI reply) | ADOPT | High | High |
| 38 | Calendar system (CRUD, ICS, CalDAV, NL parsing) | ADOPT | High | High |
| 39 | Notes system (checklists, reminders, LLM synthesis) | ADOPT | Medium | Medium |
| 40 | Documents system (living docs, PDF, AI tidy) | ADOPT | High | Medium |
| 41 | Contacts system (CardDAV, resolution) | ADOPT | Medium | Medium |
| 42 | Hybrid search pipeline (Mem0 + Graphiti + Cortex) | MERGE (M2) | High | Critical |
| 43 | LLM-based graph builder | REPLACE (R1) | High | Critical |
| 44 | Enhanced entity model | MERGE (M3) | Medium | Important |
| 45 | Bi-temporal knowledge tracking | ADAPT (AD5) | Low | Important |
| 46 | Vault settings | ADAPT (AD10) | Medium | Important |
| 47 | OpenAI-compatible API | ADOPT (A8) | Medium | Important |
| 48 | UI control tool | ADAPT | Medium | Low |
| 49 | Teacher escalation (LLM-to-LLM) | ADOPT | Low | Low |
| 50 | Agent-to-agent sessions | ADOPT | Medium | Medium |

---

## 13. High-Risk Recommendations

| Risk | Item | Mitigation |
|------|------|-----------|
| **Agent loop breakage** | R5 (unified agent loop) | Implement behind feature flag. Keep planner.py as fallback. Test with existing 486+ tests. |
| **Vector store abstraction** | R4 (Qdrant → abstracted) | Phase 2 creates Protocol only. Qdrant implementation is current default. Desktop implementation in Phase 6. |
| **Memory consolidation quality** | M1 (3-way merge) | Start with Mem0 extraction only. Add Graphiti contradiction detection in second pass. Validate against real conversations. |
| **Plugin interface stability** | AD9 (3-layer plugins) | Lock Protocol interfaces before opening to community. Version the plugin API. |
| **Context compaction quality** | A10 (structured summary) | Use cheaper/faster model for compaction. Log compaction quality. Allow manual override. |
| **Email system complexity** | 37 (IMAP/SMTP) | Start with read-only. Add send in second pass. Handle OAuth2 carefully. |
| **CalDAV compatibility** | 38 (CalDAV sync) | Test against Radicale, Nextcloud, and Google Calendar. Handle RRULE edge cases. |
| **PDF rendering** | 40 (documents system) | Use established library (pdf.js or similar). Handle forms and signatures separately. |

---

## 14. Final Priority Matrix

### By Cortex Phase

```
Phase 1: Daemon Foundation
  └── No reference repo changes needed

Phase 2: Service Abstraction ← CRITICAL BOTTLENECK
  ├── Provider abstraction (R3, R4) — unblocks everything
  ├── Tool system rebuild (R7, A9) — foundation for agents
  ├── Agent loop rebuild (R5, AD13) — replaces broken system
  ├── Context compaction (A10) — enables long conversations
  ├── Prompt security (AD16) — prevents injection
  ├── Tool policy (A11) — replaces HMAC tokens
  ├── Plugin architecture (AD9) — enables extensibility
  └── PersistentConfig (A7) — config hierarchy

Phase 3: Event Bus & Jobs
  ├── Event bus (AD15) — decouples services
  ├── Detached runs — daemon mode foundation
  ├── Run persistence (AD20) — reliable execution
  ├── Background runner (R6) — replaces asyncio tasks
  ├── Loop-breaker + completion verifier — agent quality
  ├── Session search + skill injection — agent intelligence
  ├── Context providers (AD14) — composable context
  └── MCP integration (AD11, A13) — ecosystem interop

Phase 4: CLI & Scheduler
  ├── CLI commands (AD18) — daemon management
  ├── Task scheduler — autonomous operation
  ├── Skills system — extensible skills
  ├── Model routing (AD8) — right model per task
  ├── Memory consolidation (M1) — the big memory win
  ├── Entity extraction (AD1) — graph intelligence
  ├── Indexing pipeline (AD7, A5, AD6) — search quality
  └── Daily tools foundation (webhooks, sessions, teacher)

Phase 5: API Stabilization
  ├── Hybrid search pipeline (M2) — search quality
  ├── Graph builder (R1) — graph intelligence
  ├── OpenAI-compatible API (A8) — external integration
  ├── Vault settings (AD10) — per-project config
  └── Entity model (M3) + bi-temporal (AD5)

Phase 6: Desktop Shell
  ├── Scalar quantization (AD12) — desktop vectors
  ├── Full daily productivity tools (email, calendar, etc.)
  └── Cross-encoder reranking (D1) — if GPU available

Phase 7: Web UI Transition
  └── Frontend integration of all new capabilities
```

### By Workstream (Parallel Tracks)

```
Daemon Workstream:     Phase 1 → 2 → 3 → 4 → 5 → 6 → 7
Memory Intelligence:   Phase 2 → M1 → M2 + MI-3 (graph)
Indexing Intelligence: Phase 2 → II-1 → Phase 6 → II-2
Platform Intelligence: Phase 2 → PI-1 → PI-2
Agent Intelligence:    Phase 2 → AI-1 → Phase 3 → AI-2 → AI-3
Daily Productivity:    Phase 4 → scheduler/skills → Phase 5 → email/calendar/etc.
```

### By Impact vs Effort

| | Low Effort | Medium Effort | High Effort |
|--|-----------|---------------|-------------|
| **Critical Impact** | A10 (compaction), AD16 (prompt security), A11 (tool policy), A9 (@tool), A12 (intent), loop-breaker | R7 (tool registry), AD13 (agent loop), AD9 (plugin arch), M1 (consolidation), AD8 (model routing) | R5 (agent system), R4 (vector store), M2 (search pipeline), R1 (graph builder), AD11 (MCP), AD18 (CLI) |
| **High Impact** | R2 (score normalization), SSRF, path confinement | AD14 (context providers), AD15 (event bus), AD20 (run persistence), A1 (dedup), AD1 (entity extraction), A7 (PersistentConfig), AD6 (chunking), AD7 (scan/index), A5 (cache) | R6 (background runner), AD12 (quantization), email, calendar |
| **Medium Impact** | AD5 (bi-temporal), tool schemas for existing 5 | M3 (entity model), AD3 (entity boost), AD10 (vault settings), A8 (OpenAI API), AD19 (dynamic tools), AD17 (multi-agent) | research, documents, notes, contacts |
| **Low Impact** | — | AD4 (MMR), AD2 (search recipes), teacher escalation | UI control, model serving cookbook |

---

## Appendix A: Classification Legend

| Classification | Meaning |
|---------------|---------|
| **ADOPT** | Take as-is from reference repo. Minimal adaptation needed. |
| **ADAPT** | Take the pattern/concept, modify for Cortex's architecture. |
| **MERGE** | Combine elements from 2+ reference repos + Cortex into something new. |
| **REPLACE** | Cortex's current implementation is inferior. Replace entirely. |
| **DEFER** | Valuable but not now. Specific phase or dependency listed. |
| **REJECT** | Wrong fit for Cortex. Specific reason documented. |

## Appendix B: Reference Repository Summary

| Repo | Batch | Domain | Lines Analyzed | Key Value |
|------|-------|--------|---------------|-----------|
| Mem0 | 1 | Memory | ~30,000 | V3 extraction prompts, triple-signal search, dedup, entity boost |
| Graphiti | 1 | Knowledge Graphs | ~20,000 | Temporal KG, LLM extraction, contradiction detection, MMR |
| LlamaIndex | 2 | Indexing/Retrieval | ~50,000 | Composable RAG, hierarchical chunking, 70+ vector backends |
| sist2 | 2 | Search/Indexing | ~15,000 | Two-phase scan/index, FTS5, file type detection |
| turbovec | 2 | Vector Storage | ~10,000 | Scalar quantization, SIMD flat scan, desktop vectors |
| Open WebUI | 3 | Platform | ~40,000 | PersistentConfig, SvelteKit→Next.js patterns, 6-layer plugins |
| AnythingLLM | 3 | Platform | ~35,000 | 35+ providers, workspace settings, MCP hypervisor, model routing |
| ollama-catalog | 3 | Models | ~5,000 | Model metadata, capability detection, catalog format |
| Continue | 4 | Agent/Tools | ~25,000 | IContextProvider, 18 tools, auto-compaction, MCP singleton |
| Odysseus | 4 | Agent/Productivity | ~25,000 | Streaming agent loop, 30+ tools, daily productivity (email/calendar/tasks/notes/documents/contacts), task scheduler |
| Strands Tools | 4 | Agent/Orchestration | ~15,000 | @tool decorator, use_agent, swarm, workflow DAG, MCPTool |

## Appendix C: What Odysseus Would Lose if Replaced by Cortex

| Capability | Cortex Advantage |
|------------|-----------------|
| Knowledge graph | Graph-based reasoning, community detection |
| Bi-temporal knowledge | Temporal queries, fact validity tracking |
| PostgreSQL | Scale, reliability, JSONB, 34+ tables |
| Next.js frontend | Modern React 19, SSR, component library |
| Two-password auth | Vault isolation, CSRF protection |
| Hybrid RAG | Vector + fulltext + graph + MMR |
| Model catalog | Providers, variants, benchmarks |
| Governance | GOVERNANCE.md, WORKFLOWS.md, ADRs, 486+ tests |

## Appendix D: What Cortex Would Miss if Replaced by Odysseus

| Capability | Severity | Odysseus Advantage |
|------------|----------|-------------------|
| Streaming agent loop | Critical | 3,485-line async generator with full lifecycle |
| Context compaction | Critical | Auto at 85% with structured summary |
| Tool schemas | Critical | 60+ tools with full JSON Schema |
| Tool policy | Critical | Per-turn composition vs HMAC tokens |
| Prompt security | Critical | UNTRUSTED_SOURCE_DATA guards |
| MCP integration | Critical | Full manager (stdio + SSE) |
| Detached runs | Critical | Server-side with replay buffer |
| Intent classification | Important | casual/admin/agent routing |
| Loop-breaker | Important | Stall detection + force-answer |
| Completion verifier | Important | Fresh-context LLM subagent |
| SSRF protection | Important | Private URL blocking |
| Path confinement | Important | Sensitive + allowlist + workspace |
| Daily productivity | Important | Email, calendar, tasks, notes, documents, contacts |
| Task scheduler | Important | Cron + housekeeping + personal assistant |
| Deep research | Nice-to-have | IterResearch-style multi-step research |

---

**End of Master Plan. This document supersedes all individual batch findings files.**
**After this document is committed, `docs/ref/` can be deleted.**
