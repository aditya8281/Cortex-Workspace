# Cortex Gap Analysis

## Comparison Against Reference Repos (All 3 Batches)

| Batch | Repos | Domain |
|-------|-------|--------|
| 1 | Mem0, Graphiti | Memory, knowledge graphs, consolidation, temporal |
| 2 | LlamaIndex, sist2, turbovec | Indexing, retrieval, chunking, vector storage, embeddings |
| 3 | Open WebUI, AnythingLLM, ollama-catalog | Platform, providers, models, settings, plugins, desktop |

### What Cortex Already Does Well

| Capability | Status | Quality vs Reference |
|------------|--------|---------------------|
| Confidence-based memory scoring | ✅ Implemented | **Better** — Mem0/Graphiti have no explicit confidence |
| Time-based memory decay | ✅ Implemented | **Unique** — neither reference repo does this |
| Access-count tracking | ✅ Implemented | **Better** — explicit reinforcement mechanism |
| Three-tier embedding fallback | ✅ Implemented | **Better** — more resilient than single-provider |
| Embedding cache with TTL | ✅ Implemented | **Better** — neither reference repo caches embeddings |
| Incremental indexing | ✅ Implemented | **Unique** — neither reference repo indexes code |
| 17 document parsers | ✅ Implemented | **Better** — broader document support |
| Semantic chunking | ✅ Implemented | **Comparable** — document-type-aware strategies |
| Token-budgeted RAG | ✅ Implemented | **Comparable** — Mem0/Graphiti don't do token budgeting |
| arq background tasks | ✅ Implemented | **Better** — Mem0/Graphiti are synchronous only |
| Retrieval metrics | ✅ Implemented | **Better** — Mem0/Graphiti have no metrics |
| Soft delete for memories | ✅ Implemented | **Comparable** — Mem0 uses hard delete + history |

### Critical Gaps (Must Address)

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **Memory consolidation** | None — memories created manually or via LLM extraction only | Mem0: ADD/UPDATE/DELETE pipeline with LLM dedup | Memories accumulate without cleanup, duplicates build up |
| **Memory deduplication** | None | Mem0: 3-level dedup (batch, existing, hash). Graphiti: LLM-based entity+edge dedup | Search quality degrades with duplicate memories |
| **Contradiction handling** | None — old facts stay alongside new ones | Graphiti: automatic invalidation with temporal preservation | User sees contradictory information |
| **LLM-based entity extraction** | Regex only (graph builder) | Mem0: spaCy NER. Graphiti: LLM-based NER with custom types | Misses semantic entities, can't extract relationships |
| **Temporal knowledge** | first_seen/last_seen only | Graphiti: bi-temporal (valid/invalid + created/expired) | Can't answer "what did we know on date X?" |
| **Graph-based memory linking** | None — memories and graph are separate systems | Mem0: entity→memory linking. Graphiti: episode→entity→community | No relationship-aware memory retrieval |

### Important Gaps (Should Address)

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **MMR diversity reranking** | None | Both: MMR for result diversity | Search returns redundant results |
| **Cross-encoder reranking** | None | Both: neural reranking for precision | Lower precision on complex queries |
| **Community detection** | None | Graphiti: label propagation + LLM summaries | No high-level reasoning over entity clusters |
| **Composable search** | Fixed pipeline | Graphiti: methods × rerankers × layers | Can't tune search for different use cases |
| **Action-aware embeddings** | None — same embedding for all operations | Mem0: different vectors for add/search/update | Suboptimal retrieval vs storage embeddings |
| **Entity-based search boosting** | None | Mem0: entity boost weight 0.5 | Misses entity-centric query enhancement |
| **Episodic memory model** | Conversations only | Graphiti: every input is an episode with edges | No unified episode tracking across sources |
| **Saga/conversation chaining** | None | Graphiti: NEXT_EPISODE chain + SagaNode | No conversation sequence awareness |

### Nice-to-Have Gaps (Could Address)

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **Full audit trail** | None (overwrite on update) | Mem0: SQLite history of every mutation | Can't debug memory evolution |
| **Multi-hop graph traversal** | SQL JOINs (limited) | Graphiti: Cypher BFS/DFS | Limited relationship discovery |
| **BFS graph expansion in search** | None | Graphiti: configurable depth BFS | Misses related context via graph |
| **Score explanation** | None | Mem0: explain=True mode | Hard to debug search quality |
| **Configurable search recipes** | None | Graphiti: pre-built + custom configs | Can't optimize per use case |
| **LLM-assisted dedup** | None | Both repos: LLM judges entity identity | String matching misses semantic duplicates |

### Architecture Gaps

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **Service abstraction for graph** | Concrete PostgreSQL classes | Graphiti: ABC + composite operations | Can't swap graph backend |
| **Vector store abstraction** | Qdrant-specific | Mem0: 24 swappable backends | Locked to Qdrant |
| **LLM provider abstraction** | llm_manager (basic) | Mem0: 18 providers via factory | Limited provider support |
| **Graph DB as primary store** | PostgreSQL (SQL) | Graphiti: Neo4j (native graph) | Poor graph traversal performance |
| **In-process event bus** | None | N/A (both use synchronous pipelines) | Can't decouple services for daemon mode |
| **Job system** | arq (external Redis) | N/A | Can't run embedded without Redis |

### Gap Severity Summary

| Severity | Count | Examples |
|----------|-------|---------|
| **Critical** | 6 | Memory consolidation, dedup, contradiction handling, entity extraction, temporal KG, memory-graph linking |
| **Important** | 8 | MMR, cross-encoder, community detection, composable search, action-aware embeddings, entity boosting, episodic model, saga chaining |
| **Nice-to-have** | 6 | Audit trail, multi-hop traversal, BFS expansion, score explanation, search recipes, LLM dedup |
| **Architecture** | 6 | Service abstractions, graph DB, event bus, job system |

### Alignment with Daemon-First Transition

The daemon-first transition plan (7 phases) addresses some architecture gaps (service abstraction, event bus, job system) but does NOT address the memory/graph gaps. These are orthogonal workstreams:

| Phase | Addresses Architecture Gap? | Addresses Memory/Graph Gap? |
|-------|---------------------------|---------------------------|
| 1. Daemon Foundation | ✅ | ❌ |
| 2. Service Abstraction | ✅ | ❌ |
| 3. Event Bus & Job System | ✅ | ❌ |
| 4. CLI Completion | ❌ | ❌ |
| 5. API Stabilization | ❌ | ❌ |
| 6. Desktop Shell | ❌ | ❌ |
| 7. Web UI Transition | ❌ | ❌ |

**Recommendation:** Memory/graph improvements should be a parallel workstream, not interleaved with daemon transition. The daemon transition creates the infrastructure (service abstraction, event bus) that memory/graph improvements will use.

---

## Batch 2 Gaps — Indexing, Retrieval & Search

### Critical Gaps

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **Hierarchical chunking** | Flat chunks only (max 500-800 tokens) | LlamaIndex: parent-child relationships with AutoMergingRetriever | Loses document context; can't collapse child chunks to parent |
| **IngestionCache** | None — full re-index on any content change | LlamaIndex: hash-based transform caching, skip unchanged transforms | Redundant computation on re-index; wasted embedding calls |
| **Composable pipeline** | Monolithic indexing path (one way to index everything) | LlamaIndex: every stage swappable via ABCs, pipeline assembled from components | Can't customize indexing per document type |
| **Two-phase scan/index** | Single pass: parse + embed + upsert | sist2: decoupled scan (parse) from index (ingest) phases | Can't re-index without re-parsing; no lightweight incremental |

### Important Gaps

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **Scalar quantization** | Full FP32 vectors (768-dim × 4 bytes = 3KB/vector) | turbovec: 2-4 bit quantization, 8-16× compression, comparable recall | Desktop deployment: disk/RAM usage too high for large corpora |
| **Flat scan vs HNSW** | Qdrant with HNSW (external dependency) | turbovec: SIMD flat scan over compressed data, no graph overhead | Desktop mode could skip Qdrant entirely for small collections |
| **FTS5 as first-class search** | PostgreSQL fulltext only | sist2: SQLite FTS5 with BM25 weights, no external DB needed | Desktop mode: SQLite FTS5 viable without PostgreSQL |
| **mtime-based incremental** | SHA-256 hash check (expensive) after mtime pre-filter | sist2: mtime-only change detection, skip hash unless needed | Hash is overkill for most changes; mtime alone is faster |
| **Semantic splitter** | Semantic chunker exists but basic | LlamaIndex: splits at embedding-distance boundaries, natural break points | Cortex's chunking doesn't respect semantic boundaries |
| **SentenceWindow retrieval** | None | LlamaIndex: store individual sentences, retrieve with surrounding context | Precise retrieval misses surrounding context |
| **Multi-query fusion** | RRF merge only (same query, different sources) | LlamaIndex: LLM generates query variants, each retriever runs independently | Single query limits recall; multi-query broadens coverage |
| **Response synthesis modes** | Single mode (stuff + truncate) | LlamaIndex: 7 modes (compact, refine, tree summarize, accumulate, etc.) | Can't optimize response quality per query type |

### Nice-to-Have Gaps

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **15+ file parsers** | 21 tracked extensions (code-focused) | sist2: PDF, EPUB, XLSX, PPTX, audio, video, raw images, fonts, archives | Missing non-code document formats |
| **Virtual file abstraction** | None — direct file reads | sist2: vfile_t for transparent archive-inside-archive scanning | Can't index contents of zip/tar archives |
| **Keyset pagination** | Offset-based pagination | sist2: cursor-based pagination via ROWID | Slower on large result sets |
| **Embedding optimizer** | None | LlamaIndex: optimizes embeddings for better retrieval | Post-embedding improvement opportunity |

### Alignment with Daemon Plan

| Phase | Addresses Indexing Gap? | Notes |
|-------|------------------------|-------|
| 2. Service Abstraction | ✅ Partial | Enables vector store abstraction, but not chunking/pipeline |
| 3. Event Bus & Jobs | ✅ Partial | Background indexing jobs, but not pipeline architecture |
| 6. Desktop Shell | ✅ Partial | Desktop needs quantized vectors + SQLite-only mode |

---

## Batch 3 Gaps — Platform Architecture

### Critical Gaps

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **Provider abstraction** | Inline handling in llm_manager, no formal interface | Open WebUI: file-per-provider. AnythingLLM: directory-per-provider, 35 providers | Adding a new LLM provider requires modifying core code |
| **Plugin/extension system** | None — no extensibility mechanism | Open WebUI: 6 layers (functions, tools, skills, pipelines, filters, actions). AnythingLLM: 5 layers + MCP | Users can't extend Cortex without forking |
| **MCP integration** | None | AnythingLLM: MCP hypervisor pattern (connect to external tool servers) | Can't interoperate with the MCP ecosystem |
| **Model routing** | One model for everything | AnythingLLM: rules-based routing per workspace (calculated, LLM-based, sticky, default) | Can't route different tasks to different models |

### Important Gaps

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **PersistentConfig pattern** | Env vars only, no runtime-mutable config | Open WebUI: env → DB → user (3-tier) | Can't change config at runtime without restart |
| **Per-workspace settings** | repo_id scoping only | AnythingLLM: 30+ settings per workspace (model, retrieval, search mode) | Can't customize behavior per project/vault |
| **Per-user preferences** | None | Open WebUI: user settings stored in users.settings JSON | Can't personalize per user |
| **OpenAI-compatible API** | Custom REST API only | Open WebUI: `/v1/chat/completions`. AnythingLLM: `/v1/openai` | Can't integrate with Continue, Cursor, etc. |
| **Model metadata catalog** | Basic ModelCatalog (name, family, params) | ollama-catalog: 773+ models, capability detection, cross-source availability | No capability-aware model selection |
| **Context window tracking** | None | AnythingLLM: Context Window Finder (remote JSON + cache + fallback) | Can't enforce context limits per model |
| **Multi-provider model aggregation** | Single provider at a time | Open WebUI: merges Ollama + OpenAI + custom + functions + pipelines into unified list | Can't see all available models across providers |

### Nice-to-Have Gaps

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **Community marketplace** | None | AnythingLLM: Community Hub for importing/exporting flows, prompts, commands | No ecosystem sharing |
| **Embeddable widgets** | None | AnythingLLM: standalone React widget for website integration | Can't embed Cortex in other apps |
| **Collector proxy pattern** | Inline indexing | AnythingLLM: separate Python Flask collector for document ingestion | Can't scale ingestion independently |
| **Desktop shell** | Web-only | AnythingLLM: bundled binary downloads (Mac/Win/Linux) | No native desktop experience |
| **System tray integration** | None | N/A (neither reference has this, but it's a desktop requirement) | No background daemon visibility |

### Alignment with Daemon Plan

| Phase | Addresses Platform Gap? | Notes |
|-------|------------------------|-------|
| 1. Daemon Foundation | ✅ Partial | Daemon mode enables background provider switching |
| 2. Service Abstraction | ✅ Partial | Enables provider abstraction, but not plugin system |
| 4. CLI Completion | ✅ Partial | CLI can expose provider/model management |
| 5. API Stabilization | ✅ Partial | OpenAI-compatible API fits here |
| 6. Desktop Shell | ✅ | Desktop needs system tray, auto-start, native packaging |

---

## Consolidated Gap Severity Summary

| Severity | Batch 1 | Batch 2 | Batch 3 | Total |
|----------|---------|---------|---------|-------|
| **Critical** | 6 | 4 | 4 | **14** |
| **Important** | 8 | 8 | 7 | **23** |
| **Nice-to-have** | 6 | 4 | 5 | **15** |
| **Architecture** | 6 | — | — | **6** |
| **Total** | 26 | 16 | 16 | **58** |

### Overlapping Gaps (appear in multiple batches)

| Gap | Batches | Cortex Impact |
|-----|---------|---------------|
| **Provider abstraction** | 1 (LLM provider abstraction), 3 (provider architecture) | Both batches identify this as critical |
| **Vector store abstraction** | 1 (vector store locked to Qdrant), 2 (turbovec quantization, 70+ backends) | Batch 2 adds quantization dimension |
| **Composable pipeline** | 1 (memory consolidation pipeline), 2 (LlamaIndex composable RAG) | Memory and indexing both need composable pipelines |
| **Search scoring** | 1 (triple-signal search), 2 (adaptive score normalization, BM25 sigmoid) | Batch 2 adds specific formulas to adopt |
| **MMR diversity** | 1 (missing MMR), 2 (Graphiti MMR + LlamaIndex postprocessors) | Both batches flag this |

### Non-Overlapping Gaps (unique to one batch)

| Batch | Unique Gaps |
|-------|-------------|
| 1 | Memory consolidation, dedup, contradiction handling, temporal KG, memory-graph linking |
| 2 | Hierarchical chunking, IngestionCache, scalar quantization, FTS5, multi-query fusion, response synthesis modes |
| 3 | Plugin system, MCP integration, model routing, PersistentConfig, workspace settings, OpenAI-compatible API, desktop shell |

---

## Batch 4 Gaps — Agent, Orchestration & Tool Systems

### Critical Gaps

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **Tool system** | 9 tools, no parameter schemas, no policy, no dynamic loading | Continue: 18 tools with full JSON Schema + policy. Strands: 47 tools with @tool auto-schema + hot-reload | LLM function-calling degraded without parameter schemas; can't extend tools without forking |
| **Agent execution model** | Planner→Executor two-agent, max 10 iterations, no abort, no compaction | Continue: single tool-calling loop with AbortController + auto-compaction. Odysseus: multi-turn loop with action intent classification + prompt security | Agent loop is fragile, can't handle long conversations, no cancellation |
| **Context compaction** | None — simple truncation at fixed token budget | Continue: auto at 85% context window. Odysseus: auto at 85% with structured summary (Goal/Done/State/Pending) | Long conversations lose context; no structured memory of what was accomplished |
| **Multi-agent routing** | Plan references "researcher"/"reviewer" but all route to single executor | Strands: use_agent (child delegation), swarm (decentralized handoff), workflow (DAG) | Can't use different models/tools for different subtasks |
| **CLI implementation** | 15 Commander.js stubs, zero functionality | Continue: Commander.js + Ink TUI with headless mode, sessions, slash commands. Odysseus: 20+ specialized CLIs | No command-line interface for daemon management, agent execution, or knowledge operations |

### Important Gaps

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **Context providers** | Monolithic RAG pipeline (vector + fulltext + graph) | Continue: 20+ IContextProvider implementations, parallel execution, token budgeting | Can't independently tune/reuse context sources |
| **Tool policy** | HMAC approval tokens for 3 tools | Continue: per-tool ToolPolicy with allow/deny/ask per context. Odysseus: per-turn policy composition (plan mode, guide-only) | Can't express nuanced permission rules (e.g., read-only in plan mode) |
| **Event bus** | Direct SSE streaming, no pub/sub | Odysseus: event bus + task scheduler. Events trigger scheduled tasks. | Can't decouple services for daemon mode |
| **Prompt security** | No guards on external data | Continue: untrusted context markers. Odysseus: UNTRUSTED_SOURCE_DATA guards + UNTRUSTED_CONTEXT_POLICY | Retrieved content could inject prompts |
| **Dynamic tool loading** | None — tools hardcoded at import | Strands: hot-reload from tools/ directory + load_tool() for arbitrary paths | Can't extend tools at runtime |
| **MCP integration** | None | Continue: MCPManagerSingleton. Odysseus: McpManager. Strands: MCPClient + MCPTool wrapper | Can't interoperate with MCP ecosystem |
| **Action intent classification** | None — all input goes to same path | Odysseus: regex-based routing for chat vs agent vs command | Can't distinguish "search my code" from "tell me a joke" |

### Nice-to-Have Gaps

| Gap | Cortex Current | Reference Implementation | Impact |
|-----|---------------|------------------------|--------|
| **Structured compaction summaries** | None | Odysseus: Goal/Done/State/Pending/KeyContext format | Less useful context recovery after compaction |
| **AbortController for cancellation** | None — asyncio tasks run to completion | Continue: AbortController per message, killable streams | Can't cancel in-progress agent runs |
| **Agent workspace isolation** | Agents sandboxed to ~/.cortex-agent-workspace | Continue: agents operate on real codebase. Strands: agents operate on real filesystem | Agents can't modify real project files |

### Alignment with Daemon Plan

| Phase | Addresses Agent Gap? | Notes |
|-------|---------------------|-------|
| 2. Service Abstraction | ✅ Critical | Enables tool system rebuild, provider abstraction, context provider pattern |
| 3. Event Bus & Jobs | ✅ Critical | Event bus, MCP integration, background agent runs |
| 4. CLI Completion | ✅ Critical | CLI implementation with daemon management + agent execution |
| 5. API Stabilization | ✅ Partial | OpenAI-compatible API for agent access |

---

## Consolidated Gap Severity Summary

| Severity | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Total |
|----------|---------|---------|---------|---------|-------|
| **Critical** | 6 | 4 | 4 | 5 | **19** |
| **Important** | 8 | 8 | 7 | 7 | **30** |
| **Nice-to-have** | 6 | 4 | 5 | 3 | **18** |
| **Architecture** | 6 | — | — | — | **6** |
| **Total** | 26 | 16 | 16 | 15 | **73** |

### Overlapping Gaps (appear in multiple batches)

| Gap | Batches | Cortex Impact |
|-----|---------|---------------|
| **Provider abstraction** | 1 (LLM provider abstraction), 3 (provider architecture) | Both batches identify this as critical |
| **Vector store abstraction** | 1 (vector store locked to Qdrant), 2 (turbovec quantization, 70+ backends) | Batch 2 adds quantization dimension |
| **Composable pipeline** | 1 (memory consolidation pipeline), 2 (LlamaIndex composable RAG) | Memory and indexing both need composable pipelines |
| **Search scoring** | 1 (triple-signal search), 2 (adaptive score normalization, BM25 sigmoid) | Batch 2 adds specific formulas to adopt |
| **MMR diversity** | 1 (missing MMR), 2 (Graphiti MMR + LlamaIndex postprocessors) | Both batches flag this |
| **MCP integration** | 3 (MCP hypervisor), 4 (MCP in all 3 repos) | Batch 4 confirms MCP is table stakes across agent platforms |
| **Multi-agent orchestration** | 4 (use_agent, swarm, workflow) | Cortex's planner→executor is the weakest agent model across all repos |
| **Context management** | 4 (context providers, compaction, prompt security) | Cortex is the only repo without context compaction |

### Non-Overlapping Gaps (unique to one batch)

| Batch | Unique Gaps |
|-------|-------------|
| 1 | Memory consolidation, dedup, contradiction handling, temporal KG, memory-graph linking |
| 2 | Hierarchical chunking, IngestionCache, scalar quantization, FTS5, multi-query fusion, response synthesis modes |
| 3 | Plugin system, model routing, PersistentConfig, workspace settings, OpenAI-compatible API, desktop shell |
| 4 | Tool system rebuild, agent execution model, context compaction, multi-agent routing, CLI implementation, context providers, tool policy, event bus, prompt security, dynamic tool loading, action intent classification |
