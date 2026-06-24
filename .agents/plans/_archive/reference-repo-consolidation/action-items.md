# Action Items

**Date:** 2026-06-25
**Covers:** All 4 batches (Memory, Indexing, Platform, Agent)

---

## Immediate (Before Daemon Phase 2 Completes)

### AI-1. Study Mem0 Consolidation Prompts
**Priority:** P0
**Owner:** Human
**Depends on:** Nothing
**Effort:** 1-2 hours reading

Read these specific files in `docs/ref/mem0/`:
- `mem0/configs/prompts.py` — the V3 extraction and consolidation prompts (this is the core intelligence)
- `mem0/memory/main.py` — the `_add_to_vector_store()` and `_update_memory()` methods
- `mem0/utils/entity_extraction.py` — entity extraction logic

Extract the exact prompt templates. These will be adapted (not copied) for Cortex's consolidation pipeline.

### AI-2. Study Graphiti Edge Invalidation Prompts
**Priority:** P0
**Owner:** Human
**Depends on:** Nothing
**Effort:** 1-2 hours reading

Read these specific files in `docs/ref/graphiti/`:
- `graphiti_core/prompts/` directory — all prompt templates (extract, dedupe, summarize)
- `graphiti_core/graphiti.py` — the `add_episode()` method (main orchestration)
- `graphiti_core/edges.py` — EntityEdge model

Extract the exact prompt templates for entity extraction, edge deduplication, and contradiction detection.

### AI-3. Study Provider Abstraction Patterns
**Priority:** P0
**Owner:** Human
**Depends on:** Nothing
**Effort:** 1-2 hours reading

Read these specific files in `docs/ref/`:
- `open-webui/backend/open_webui/env.py` — PersistentConfig environment variables
- `open-webui/backend/open_webui/configs/` — PersistentConfig class implementation
- `anything-llm/server/utils/AiProviders/` — one provider directory (e.g., `ollama/`) to see convention-based interface
- `ollama-catalog/src/ollama_catalog/` — model metadata and capability detection

Extract: PersistentConfig pattern, provider interface conventions, model metadata schema.

---

## After Daemon Phase 2 (Service Abstraction) Completes

### AI-4. Implement PI-1: Provider Abstraction & Plugin System
**Priority:** P1 (highest — unblocks all other workstreams)
**Owner:** Agent
**Depends on:** Daemon Phase 2 complete
**Effort:** Large (new subsystem)

Implement in order:
1. `backend/app/core/providers/protocol.py` — LLMProvider, EmbeddingProvider, VectorStore Protocol definitions
2. `backend/app/core/providers/factory.py` — Provider factory + registration
3. Refactor `llm_manager` to use Protocol interface
4. Refactor `embedding_service` to use Protocol interface (R3)
5. `backend/app/plugins/base.py` — Plugin Protocol definitions
6. `backend/app/plugins/registry.py` — Plugin discovery + registration
7. `backend/app/services/mcp/hypervisor.py` — MCP client lifecycle (AD11)
8. `backend/app/services/mcp/server.py` — MCP server (expose Cortex tools)
9. Migration: add `provider_config` JSON to vault settings
10. Tests: TDD for each component

### AI-5. Implement MI-1: Memory Consolidation Foundation
**Priority:** P1
**Owner:** Agent
**Depends on:** AI-3 spec approved, Daemon Phase 2 complete, AI-4 (needs abstracted LLM)
**Effort:** Large (new subsystem)

Implement in order:
1. `backend/app/services/memory/entity_extraction.py` — LLM-based entity extraction
2. `backend/app/services/memory/deduplication.py` — 3-level dedup
3. `backend/app/services/memory/contradiction_detector.py` — contradiction detection
4. `backend/app/services/memory/temporal.py` — bi-temporal tracking
5. `backend/app/services/memory/consolidation.py` — orchestrator
6. Migration: add `valid_at`, `invalid_at` to LongTermMemory
7. Migration: add `entity_source`, `linked_memory_ids`, `summary`, `labels` to GraphNode
8. Tests: TDD for each component

### AI-6. Implement II-1: Indexing Pipeline Refactoring
**Priority:** P2
**Owner:** Agent
**Depends on:** Daemon Phase 2 complete, AI-4 (needs vector store abstraction)
**Effort:** Medium

Implement in order:
1. `backend/app/services/indexing/ingestion_cache.py` — hash-based transform caching (A5)
2. `backend/app/services/indexing/scan_phase.py` — mtime-based change detection (AD7)
3. Refactor `IncrementalIndexer` to use two-phase scan/index (AD7)
4. Add parent-child relationships to chunker (AD6)
5. Migration: add `parent_chunk_id` to DocumentChunk
6. Migration: add `ingestion_cache` table
7. Tests: TDD for cache invalidation, scan/index separation, hierarchical chunking

### AI-7. Implement PI-2: Model Management & Settings
**Priority:** P2
**Owner:** Agent
**Depends on:** AI-4 complete (needs provider abstraction)
**Effort:** Medium

Implement in order:
1. `backend/app/core/persistent_config.py` — Env → DB → User config hierarchy (A7)
2. `backend/app/services/models/model_router.py` — rules-based routing per vault (AD8)
3. `backend/app/services/models/context_window_finder.py` — remote JSON + cache + fallback
4. `backend/app/api/v1/openai_compat.py` — OpenAI-compatible API endpoints (A8)
5. Vault settings API: GET/PUT `/api/v1/vaults/{vault_id}/settings` (AD10)
6. Migration: add `model_routing_rules` table
7. Migration: add `user_preferences` table
8. Migration: add `system_settings` table
9. Tests: TDD for PersistentConfig, model routing, OpenAI API compat

---

## After MI-1 Complete

### AI-8. Implement MI-2: Search Intelligence
**Priority:** P2
**Owner:** Agent
**Depends on:** AI-5 (MI-1) complete
**Effort:** Medium

Implement in order:
1. `backend/app/services/retrieval/score_fusion.py` — adaptive score normalization (R2)
2. `backend/app/services/retrieval/entity_boost.py` — entity-based boosting (AD3)
3. `backend/app/services/retrieval/rerankers/mmr.py` — MMR diversity (AD4)
4. `backend/app/services/retrieval/search_config.py` — composable recipes (AD2)
5. Refactor `HybridRetrievalV2` → `HybridRetrievalV3`
6. Tests: search quality regression tests

### AI-9. Implement MI-3: Graph Intelligence
**Priority:** P3
**Owner:** Agent
**Depends on:** AI-5 (MI-1), AI-8 (MI-2) complete
**Effort:** Large

Implement in order:
1. `backend/app/services/graph/llm_graph_builder.py` — LLM-based extraction (R1)
2. `backend/app/services/graph/community_detector.py` — label propagation (D2, now unblocked)
3. `backend/app/services/graph/graph_traversal.py` — multi-hop traversal (D4, now unblocked)
4. `backend/app/services/graph/entity_hydration.py` — entity summaries
5. Replace regex-based graph builder
6. Tests: graph quality tests

---

## After Phase 6 (Desktop Shell)

### AI-10. Implement II-2: Desktop-Ready Vector Storage
**Priority:** P3
**Owner:** Agent
**Depends on:** Phase 6 (Desktop Shell), AI-6 (vector store abstraction)
**Effort:** High

Implement in order:
1. `backend/app/services/vector_db/quantized_store.py` — turbovec binding (AD12)
2. `backend/app/services/vector_db/sqlite_fts5.py` — FTS5 search for desktop mode
3. Desktop mode config: auto-select quantized store when Qdrant unavailable
4. Tests: quantized vector quality, desktop mode integration

---

## Agent Intelligence Workstream (Batch 4)

### AI-13. Implement AI-1: Agent System Foundation
**Priority:** P0 (highest — weakest subsystem in Cortex)
**Owner:** Agent
**Depends on:** Daemon Phase 2 complete, AI-4 (provider abstraction)
**Effort:** Large (core system rewrite)

Implement in order:
1. `backend/app/agents/tools/__init__.py` — `@tool` decorator with auto-schema from type hints + docstrings (A9)
2. `backend/app/agents/tools/registry.py` — tool discovery, validation, dynamic loading (AD19, R7)
3. `backend/app/agents/policy.py` — ToolPolicy composition: allow/deny/ask per context (A11)
4. `backend/app/agents/loop.py` — unified agent loop with tool-calling, policy, abort (R5, AD13)
5. `backend/app/services/context/compaction.py` — auto-compaction at 85% with structured summary (A10)
6. `backend/app/services/context/security.py` — UNTRUSTED_SOURCE_DATA markers (AD16)
7. `backend/app/services/context/providers/__init__.py` — ContextProvider Protocol (AD14)
8. Refactor existing tools to use @tool decorator
9. Replace planner.py + executor.py with loop.py
10. Tests: TDD for decorator, registry, policy, loop, compaction

### AI-14. Implement AI-2: CLI & Event Bus
**Priority:** P1
**Owner:** Agent
**Depends on:** Daemon Phase 3 complete (event bus + background jobs)
**Effort:** Large (many commands, but incremental)

Implement in order:
1. `backend/app/services/events/bus.py` — pub/sub event bus with Redis backing (AD15)
2. `backend/app/services/events/scheduler.py` — event-triggered task scheduling
3. `backend/app/services/intent/classifier.py` — action intent classification (A12)
4. `backend/app/services/runner/manager.py` — background agent run manager with PID tracking (AD20, R6)
5. `backend/app/services/runner/persistence.py` — orphan detection + restart-safety
6. `cli/src/commands/daemon.ts` — daemon start/stop/status/logs (AD18)
7. `cli/src/commands/agent.ts` — agent run/chat/list
8. `cli/src/commands/index.ts` — index run/status
9. `cli/src/commands/search.ts` — search "query"
10. `cli/src/commands/config.ts` — config set/get/list
11. `cli/src/commands/vault.ts` — vault lock/unlock/status
12. Tests: TDD for each component

### AI-15. Implement AI-3: MCP & Multi-Agent
**Priority:** P2
**Owner:** Agent
**Depends on:** AI-13 (agent system foundation) complete, AI-4 (plugin system) complete
**Effort:** Medium

Implement in order:
1. `backend/app/services/mcp/client.py` — MCP client (stdio + SSE transport) (A13)
2. `backend/app/agents/tools/mcp_tool.py` — MCPTool wrapper (A13)
3. `backend/app/services/mcp/registry.py` — registered MCP server configs
4. `backend/app/agents/tools/use_agent.py` — multi-agent delegation tool (AD17)
5. Integration with model routing (AI-7) for child agent model selection
6. Tests: TDD for MCP client, MCPTool wrapper, use_agent delegation

---

## Ongoing

### AI-11. Update Documentation
**Priority:** P2
**Owner:** Agent
**Depends on:** AI-5, AI-8, AI-9 (update after each completes)
**Effort:** Low

Update these docs after each phase:
- `docs/ARCHITECTURE.md` — add provider abstraction, plugin system, memory consolidation, search intelligence, graph intelligence sections
- `docs/DATABASE.md` — add new models/tables
- `CLAUDE.md` — update architecture summary
- `docs/superpowers/specs/2026-06-25-cortex-reorientation-design.md` — cross-reference all workstreams

### AI-12. Create Skills from Reusable Patterns
**Priority:** P3
**Owner:** Agent
**Depends on:** AI-5, AI-8, AI-9, AI-7 complete
**Effort:** Low

Identify reusable patterns and create skills:
- `memory-consolidation` — the two-phase extraction + consolidation pattern
- `entity-extraction` — LLM-based NER with custom types
- `hybrid-search` — adaptive scoring + entity boost + MMR
- `provider-abstraction` — Protocol-based provider registration pattern
- `plugin-system` — layered plugin registration pattern
- `agent-loop` — unified agent loop with tool-calling + policy + compaction
- `mcp-integration` — MCP client wrapper + tool wrapping pattern
- `cli-daemon` — Commander.js CLI with daemon management commands

---

## Dependency Summary

```
AI-1 (Mem0 prompts) ─────┐
                          ├──→ AI-3 (Design consolidation) ──→ AI-5 (MI-1) ──→ AI-8 (MI-2) ──→ AI-9 (MI-3)
AI-2 (Graphiti prompts) ──┘         │                         │
                                    │                         ├──→ AI-11 (docs)
AI-3 (Provider patterns) ──────────→ AI-4 (PI-1) ──→ AI-7 (PI-2)
                                    │                   │
Daemon Phase 2 ─────────────────────┘                   ├──→ AI-11 (docs)
                                                         │
Phase 6 (Desktop) ──→ AI-10 (II-2)                      │
                                                         │
Daemon Phase 2 ──→ AI-6 (II-1)                          │
                                                         │
AI-13 (Agent loop) ──→ AI-14 (CLI) ──→ AI-15 (MCP)      │
                  │              │              │         │
                  └──────────────┴──────────────┘────────┘
```

## Cross-Reference to Phase Plan

| Action Item | Aligns With | Daemon Phase | Workstream |
|-------------|-------------|--------------|------------|
| AI-1, AI-2, AI-3 | Research/Design | Anytime / After Phase 2 | Memory Intelligence |
| AI-4 | PI-1: Providers + Plugins | After Phase 2 | Platform Intelligence |
| AI-5 | MI-1: Memory Consolidation | After Phase 2 | Memory Intelligence |
| AI-6 | II-1: Indexing Pipeline | After Phase 2 | Indexing Intelligence |
| AI-7 | PI-2: Model Mgmt + Settings | After PI-1 | Platform Intelligence |
| AI-8 | MI-2: Search Intelligence | After MI-1 | Memory Intelligence |
| AI-9 | MI-3: Graph Intelligence | After MI-1 + MI-2 | Memory Intelligence |
| AI-10 | II-2: Desktop Vector Storage | After Phase 6 | Indexing Intelligence |
| AI-11 | Documentation | After each phase | All |
| AI-12 | Skill Creation | After all phases | All |
| AI-13 | AI-1: Agent System Foundation | After Phase 2 | Agent Intelligence |
| AI-14 | AI-2: CLI & Event Bus | After Phase 3 | Agent Intelligence |
| AI-15 | AI-3: MCP & Multi-Agent | After AI-1 + PI-1 | Agent Intelligence |
