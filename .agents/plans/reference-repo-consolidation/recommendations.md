# Recommendations

## Classification System

| Classification | Meaning |
|---------------|---------|
| **ADOPT** | Take as-is from reference repo. Low adaptation needed. |
| **ADAPT** | Take the pattern, but modify significantly for Cortex's context. |
| **MERGE** | Combine elements from multiple references with Cortex's existing. |
| **REPLACE** | Cortex's current implementation should be replaced entirely. |
| **DEFER** | Valuable but not now. Wait for prerequisite work. |
| **REJECT** | Considered and dismissed. Wrong fit for Cortex. |

---

## ADOPT (Take as-is or near-as-is)

### A1. Memory Deduplication Pipeline (from Mem0)
**Classification:** ADOPT
**Source:** Mem0 V3 additive extraction + consolidation

Extract Mem0's two-phase approach:
1. **Extraction phase:** LLM extracts facts from conversations (ADD-only)
2. **Consolidation phase:** LLM compares new facts against existing memories → ADD/UPDATE/DELETE/NONE

Adapt to Cortex by replacing Mem0's vector-store-only storage with Cortex's PostgreSQL + Qdrant dual-store.

**Implementation:** `backend/app/services/memory/consolidation.py`
**Effort:** Medium (prompt engineering + integration)
**Impact:** Critical — eliminates memory accumulation without cleanup

### A2. Triple-Signal Search Scoring (from Mem0)
**Classification:** ADOPT
**Source:** Mem0 score_and_rank with adaptive normalization

Take the adaptive score fusion formula:
```python
max_possible = {
    "semantic_only": 1.0,
    "semantic_bm25": 2.0,
    "semantic_entity": 1.5,
    "all_three": 2.5
}
combined = (semantic + bm25 + entity_boost) / max_possible
```

**Implementation:** Replace score normalization in `HybridRetrievalV2`
**Effort:** Low (formula change)
**Impact:** Important — better search quality with adaptive scoring

### A3. Query-Length-Adaptive BM25 Sigmoid (from Mem0)
**Classification:** ADOPT
**Source:** Mem0 BM25 normalization

Take the sigmoid parameters that adapt to query length:
```python
SIGMOID_PARAMS = {
    3: (5.0, 0.7),    # ≤3 terms
    6: (7.0, 0.6),    # ≤6 terms
    9: (9.0, 0.5),    # ≤9 terms
    15: (10.0, 0.5),  # ≤15 terms
    float('inf'): (12.0, 0.5)  # >15 terms
}
```

**Implementation:** Replace BM25 normalization in fulltext search
**Effort:** Low (pure math)
**Impact:** Important — prevents short queries from dominating scores

### A4. Embedding Cache with TTL (already implemented)
**Classification:** ADOPT (already done)
**Source:** Cortex already has this — Mem0 doesn't

Cortex's embedding cache (PostgreSQL, 30-day TTL, access tracking) is better than both reference repos. Keep as-is.

### A5. IngestionCache — Hash-Based Transform Caching (from LlamaIndex)
**Classification:** ADOPT
**Source:** LlamaIndex IngestionCache

Take the hash-based caching pattern:
- Hash input content → cache transform results
- On re-index, skip transforms where input hasn't changed
- Avoids redundant embedding calls and chunking computation

**Implementation:** `backend/app/services/indexing/ingestion_cache.py`
**Effort:** Medium (cache layer + invalidation logic)
**Impact:** Critical — eliminates redundant work on re-index
**Affected subsystem:** Indexing pipeline
**Phase:** After Phase 2 (service abstraction enables pluggable storage)

### A6. Query-Length-Adaptive BM25 Sigmoid (from Mem0 + LlamaIndex)
**Classification:** ADOPT
**Source:** Mem0 BM25 normalization + LlamaIndex hybrid search

Take the sigmoid parameters that adapt to query length (already in recommendations as A3 — extend with LlamaIndex's fusion modes):
- RRF (reciprocal rank fusion, k=60) — already implemented
- Relative score fusion — useful for multi-source
- Distance-based fusion — useful for embedding + keyword

**Implementation:** Extend `HybridRetrievalV2.score_and_rank()`
**Effort:** Low (formula additions)
**Impact:** Important — better multi-source fusion
**Affected subsystem:** Retrieval pipeline
**Phase:** After MI-1 (consolidation foundation)

### A7. PersistentConfig Pattern (from Open WebUI)
**Classification:** ADOPT
**Source:** Open WebUI PersistentConfig (env → DB → user)

Take the 3-tier configuration pattern:
```python
class PersistentConfig:
    """Config value that syncs between memory and database"""
    # Tier 1: Env var (immutable default)
    # Tier 2: DB value (runtime-mutable)
    # Tier 3: User override (per-user)
```

**Implementation:** `backend/app/core/config.py` (extend existing Settings)
**Effort:** Medium (new config class + migration for settings table)
**Impact:** Critical — enables runtime config without restart
**Affected subsystem:** Core config
**Phase:** Phase 2 (service abstraction) or Phase 5 (API stabilization)

### A8. OpenAI-Compatible API (from Open WebUI + AnythingLLM)
**Classification:** ADOPT
**Source:** Open WebUI `/v1/chat/completions`, AnythingLLM `/v1/openai`

Expose Cortex capabilities via standard OpenAI-compatible API:
- `/v1/chat/completions` — chat with memory context
- `/v1/models` — list available models
- `/v1/embeddings` — embedding generation

**Implementation:** `backend/app/api/v1/openai_compat.py`
**Effort:** Medium (new router, response format mapping)
**Impact:** Critical — enables integration with Continue, Cursor, and any OpenAI-compatible client
**Affected subsystem:** API layer
**Phase:** Phase 5 (API stabilization)

---

## ADAPT (Take pattern, modify for Cortex)

### AD1. Entity Extraction → LLM-Based (from Graphiti)
**Classification:** ADAPT
**Source:** Graphiti LLM-based NER + custom entity types

Take Graphiti's approach of using LLM for entity extraction instead of regex/spaCy. But adapt:
- Cortex should define entity types relevant to its domain (People, Projects, Tools, Concepts, Files)
- Use the LLM's existing capabilities (no spaCy dependency)
- Store extracted entities in the existing `graph_nodes` table with a new `entity_source` field

**Implementation:** `backend/app/services/memory/entity_extraction.py`
**Effort:** Medium (prompt engineering + model integration)
**Impact:** Critical — current regex extraction misses semantic entities

### AD2. Composable Search Recipes (from Graphiti)
**Classification:** ADAPT
**Source:** Graphiti SearchConfig with methods × rerankers × layers

Take the composable search pattern but simplify for Cortex:
- Define search configs as Pydantic models (not per-layer, but per-use-case)
- Provide 3-4 pre-built recipes: Code Search, Memory Search, Knowledge Search, Universal
- Allow config override via API parameters

**Implementation:** `backend/app/services/retrieval/search_config.py`
**Effort:** Medium
**Impact:** Important — enables search tuning per use case

### AD3. Entity Boosting During Search (from Mem0)
**Classification:** ADAPT
**Source:** Mem0 _compute_entity_boosts

Take the entity boost pattern but adapt for Cortex's graph:
- Extract entities from query (via LLM, not spaCy)
- Look up related memories/nodes via graph edges
- Boost search results that are entity-connected

**Implementation:** Add entity boost step to HybridRetrievalV2
**Effort:** Medium
**Impact:** Important — entity-aware retrieval

### AD4. MMR Diversity Reranking (from Graphiti)
**Classification:** ADAPT
**Source:** Graphiti MMR reranker

Take MMR (Maximal Marginal Relevance) but implement as a post-processing step:
```python
def mmr_rerank(query_embedding, results, lambda_param=0.5, top_k=10):
    # Balance relevance with diversity
    # Select results that are both relevant and diverse
```

**Implementation:** `backend/app/services/retrieval/rerankers/mmr.py`
**Effort:** Low (well-known algorithm)
**Impact:** Important — prevents redundant search results

### AD5. Bi-Temporal Knowledge Tracking (from Graphiti)
**Classification:** ADAPT
**Source:** Graphiti valid_at/invalid_at + created_at/expired_at

Take the bi-temporal model but simplify for Cortex:
- Add `valid_at` / `invalid_at` to `LongTermMemory` (when fact was true in reality)
- Keep `created_at` / `updated_at` (when recorded in system)
- Don't add `expired_at` — use `is_active` flag instead (Cortex already has soft delete)

**Implementation:** Migration + model update
**Effort:** Low (schema change + prompt update)
**Impact:** Important — enables temporal queries

### AD6. Hierarchical Chunking with Parent-Child (from LlamaIndex)
**Classification:** ADAPT
**Source:** LlamaIndex HierarchicalNodeParser + AutoMergingRetriever

Take the parent-child chunking pattern but adapt for Cortex:
- Cortex already has document-type-aware chunking (Markdown headings, code symbols, notebook cells)
- Add parent-child relationships: small retrieval chunks link to larger parent context chunks
- On retrieval, if enough children of a parent are retrieved, collapse to parent for context
- Store parent reference in chunk metadata

**Implementation:** Modify `backend/app/services/indexing/chunker.py` + `semantic_chunker.py`
**Effort:** Medium (chunk metadata changes + retrieval logic)
**Impact:** Critical — retrieves precise chunks but provides parent context
**Affected subsystem:** Indexing + Retrieval
**Phase:** After Phase 2 (service abstraction)

### AD7. Two-Phase Scan/Index Separation (from sist2)
**Classification:** ADAPT
**Source:**sist2 two-phase architecture

Take the scan/index separation but adapt for Cortex:
- Phase 1 (Scan): Walk directory, detect changes (mtime-based), parse files, extract text + metadata
- Phase 2 (Index): Chunk, embed, upsert to vector store
- Decouple so scan results can be cached and re-indexed without re-parsing
- Cortex already has batch + real-time tracks; this refines the batch track

**Implementation:** Refactor `IncrementalIndexer` + `IndexingOrchestrator`
**Effort:** Medium (pipeline refactor)
**Impact:** Important — enables incremental re-index without re-parsing
**Affected subsystem:** Indexing pipeline
**Phase:** Phase 2-3 (service abstraction + event bus)

### AD8. Model Routing (from AnythingLLM)
**Classification:** ADAPT
**Source:** AnythingLLM AnythingLLMModelRouter

Take the rules-based routing pattern but simplify for Cortex:
- Route different queries to different models based on task type
- Start with 2 rules: code tasks → code model, general → default model
- Add sticky routing (previous model stays if not expired)
- Store routing config per vault (workspace equivalent)

**Implementation:** `backend/app/services/models/model_router.py`
**Effort:** Medium (router + rule engine + vault config)
**Impact:** Critical — daemon can use right model for right task
**Affected subsystem:** Model management + vault config
**Phase:** After Phase 2 (service abstraction) — needs provider abstraction

### AD9. Plugin Architecture — 3-Layer Start (from Open WebUI + AnythingLLM)
**Classification:** ADAPT
**Source:** Open WebUI 6 layers + AnythingLLM 5 layers + MCP

Take the layered plugin concept but start with 3 layers for daemon mode:
- **Layer 1: Providers** — LLM, embedding, vector store (formal Protocol interfaces)
- **Layer 2: Tools** — Function-calling tools (MCP-compatible)
- **Layer 3: Pipelines** — Processing chains (indexing, consolidation, retrieval)

Don't implement filters/actions/skills yet — start minimal, expand later.

**Implementation:** `backend/app/plugins/` directory with Protocol-based registration
**Effort:** High (new subsystem + provider refactoring)
**Impact:** Critical — enables extensibility without forking
**Affected subsystem:** All (provider, tool, pipeline registration)
**Phase:** Phase 2-3 (service abstraction + event bus)

### AD10. Workspace/Vault Settings (from AnythingLLM)
**Classification:** ADAPT
**Source:** AnythingLLM workspace settings (~30+ fields per workspace)

Take the per-workspace settings pattern but adapt for Cortex's vault concept:
- Each vault gets: model config, embedding config, indexing rules, retrieval settings, memory scope
- Store as JSON in vault settings column
- API: GET/PUT `/api/v1/vaults/{vault_id}/settings`

**Implementation:** Migration (add settings JSON to vault model) + API router
**Effort:** Medium (migration + API + frontend settings UI)
**Impact:** Important — per-project customization
**Affected subsystem:** Vault + settings
**Phase:** Phase 5 (API stabilization)

### AD11. MCP Integration — Hypervisor Pattern (from AnythingLLM)
**Classification:** ADAPT
**Source:** AnythingLLM MCP hypervisor

Take the MCP hypervisor pattern for Cortex daemon:
- Cortex acts as MCP client: connects to external tool servers (filesystem, GitHub, etc.)
- Cortex acts as MCP server: exposes its own tools (search, memory, graph) to other MCP clients
- Lifecycle management: start, stop, health-check external MCP servers

**Implementation:** `backend/app/services/mcp/hypervisor.py` + `backend/app/services/mcp/server.py`
**Effort:** High (MCP protocol implementation + lifecycle management)
**Impact:** Critical — enables ecosystem interop
**Affected subsystem:** Tool system + daemon
**Phase:** Phase 3 (event bus) — MCP needs async message handling

### AD12. Scalar Quantization for Desktop (from turbovec)
**Classification:** ADAPT
**Source:** turbovec TurboQuant (2/3/4-bit compression)

Take the quantization concept but adapt for Cortex desktop mode:
- For desktop: 4-bit quantized vectors (8× compression, comparable recall)
- For server: keep FP32 vectors in Qdrant (no compression needed)
- SIMD-accelerated flat scan for small collections (<100K vectors)
- Skip Qdrant dependency for desktop mode entirely

**Implementation:** `backend/app/services/vector_db/quantized_store.py` (new)
**Effort:** High (Rust extension or Python binding to turbovec)
**Impact:** Important — enables desktop deployment without Qdrant
**Affected subsystem:** Vector storage
**Phase:** Phase 6 (desktop shell)

---

## MERGE (Combine multiple sources)

### M1. Memory Consolidation Pipeline (Mem0 + Graphiti + Cortex)
**Classification:** MERGE
**Sources:** Mem0 V3 extraction, Graphiti edge invalidation, Cortex confidence/decay

Combine:
- **Mem0:** Two-phase extraction (ADD-only extraction + consolidation)
- **Graphiti:** Automatic contradiction detection + invalidation
- **Cortex:** Confidence scoring + time-based decay

Result: A consolidation pipeline that:
1. Extracts new facts from conversations (ADD-only)
2. Compares against existing memories (dedup + contradiction detection)
3. Assigns confidence scores (Cortex's model)
4. Invalidates contradicted memories (Graphiti's model, not hard delete)
5. Applies decay over time (Cortex's model)

**Implementation:** `backend/app/services/memory/consolidation.py`
**Effort:** High (new subsystem)
**Impact:** Critical — the single most impactful improvement

### M2. Hybrid Search Pipeline (Mem0 + Graphiti + Cortex)
**Classification:** MERGE
**Sources:** Mem0 triple-signal, Graphiti multi-layer, Cortex hybrid retrieval

Combine:
- **Cortex:** Three sources (vector + fulltext + graph) — keep as base
- **Mem0:** Adaptive score normalization — replace basic normalization
- **Graphiti:** MMR diversity — add as post-processing
- **Mem0:** Entity boosting — add as scoring signal

Result: A search pipeline that:
1. Runs vector + fulltext + graph in parallel (Cortex current)
2. Normalizes scores adaptively (Mem0 pattern)
3. Adds entity boost scoring (Mem0 pattern)
4. Applies MMR diversity reranking (Graphiti pattern)
5. Returns token-budgeted results (Cortex current)

**Implementation:** Refactor `HybridRetrievalV2`
**Effort:** High (major refactor)
**Impact:** Critical — search quality improvement

### M3. Entity Model (Mem0 + Graphiti + Cortex)
**Classification:** MERGE
**Sources:** Mem0 entity store, Graphiti EntityNode, Cortex GraphNode

Combine:
- **Cortex:** GraphNode with node_type, name, embedding — keep as base
- **Mem0:** linked_memory_ids — add cross-references between entities and memories
- **Graphiti:** EntityNode with summary, labels, attributes — add metadata richness

Result: Enhanced GraphNode with:
- `entity_source` field (code, conversation, document)
- `linked_memory_ids` JSON field (cross-reference to LongTermMemory)
- `summary` field (LLM-generated entity summary)
- `labels` JSON field (entity type tags)

**Implementation:** Migration + model update
**Effort:** Medium
**Impact:** Important — richer entity model

---

## REPLACE (Replace Cortex's current implementation)

### R1. Graph Builder → LLM-Based Extraction (Replace Regex)
**Classification:** REPLACE
**Source:** Graphiti LLM-based extraction

Current Cortex graph builder uses regex patterns for edge extraction. Replace with LLM-based extraction:
- LLM extracts entities + relationships from code/docs/conversations
- Supports custom entity types (not just code symbols)
- Handles natural language relationships (not just calls/imports)

**Implementation:** `backend/app/services/graph/llm_graph_builder.py`
**Effort:** High (new subsystem + prompt engineering)
**Impact:** Critical — current regex extraction is too brittle

### R2. Score Normalization → Adaptive Formula (Replace Basic Normalization)
**Classification:** REPLACE
**Source:** Mem0 adaptive normalization

Current Cortex normalizes scores by source. Replace with adaptive formula that considers which signals are available.

**Implementation:** Modify `HybridRetrievalV2.score_and_rank()`
**Effort:** Low
**Impact:** Important

### R3. Embedding Service → Pluggable Provider (Replace Hardcoded Tiers)
**Classification:** REPLACE
**Source:** AnythingLLM 15 embedding engines, LlamaIndex 70+ backends

Current Cortex has hardcoded three-tier fallback (ONNX → Ollama → Mock). Replace with pluggable provider registry:
- Register embedding providers via Protocol interface
- Each provider: `embed(texts) → vectors`, `dimension() → int`
- Runtime switching via config
- Desktop mode: ONNX only (no Ollama needed)
- Server mode: Ollama, OpenAI, or any registered provider

**Implementation:** `backend/app/services/embedding/provider.py` + registry
**Effort:** Medium (new abstraction layer)
**Impact:** Important — enables provider extensibility
**Affected subsystem:** Embedding service
**Phase:** Phase 2 (service abstraction)

### R4. Vector Store → Abstracted Interface (Replace Qdrant-Only)
**Classification:** REPLACE
**Source:** AnythingLLM 10 vector DBs, LlamaIndex 70+ backends, turbovec quantized store

Current Cortex is Qdrant-only. Replace with abstracted vector store interface:
- Protocol: `upsert()`, `search()`, `delete()`, `count()`
- Desktop mode: turbovec quantized store (in-process, no Qdrant)
- Server mode: Qdrant (current) or any registered backend
- Migration path: Phase 2 abstraction, Phase 6 desktop swap

**Implementation:** `backend/app/services/vector_db/provider.py` + registry
**Effort:** High (new abstraction + multiple backend implementations)
**Impact:** Critical — enables desktop mode without Qdrant
**Affected subsystem:** Vector storage
**Phase:** Phase 2 (abstraction) + Phase 6 (desktop implementation)

---

## DEFER (Valuable but not now)

### D1. Cross-Encoder Reranking
**Classification:** DEFER
**Reason:** Requires model hosting (GPU) or API dependency. Wait until daemon mode supports optional GPU acceleration.
**When:** Phase 6-7 (Desktop Shell era, when GPU acceleration is available)

### D2. Community Detection (Label Propagation + LLM Summaries)
**Classification:** DEFER
**Reason:** Requires a richer entity graph first. Build entity extraction and temporal KG before clustering.
**When:** After M3 (entity model enhancement) is complete

### D3. Saga Pattern for Episode Sequences
**Classification:** DEFER
**Reason:** Cortex's conversation model is sufficient for now. Saga pattern adds complexity without immediate value.
**When:** When cross-session continuity becomes a priority

### D4. Multi-Hop Graph Traversal (Cypher/BFS)
**Classification:** DEFER
**Reason:** Requires graph DB migration (PostgreSQL → Neo4j or embedded graph). Wait until service abstraction phase.
**When:** Phase 2-3 (service abstraction enables graph DB swap)

### D5. Action-Aware Embeddings
**Classification:** DEFER
**Reason:** Requires embedding model that supports action-aware prompts (not all models do). Wait until embedding service is abstracted.
**When:** Phase 2 (service abstraction)

### D6. Full Audit Trail (Memory Version History)
**Classification:** DEFER
**Reason:** Useful for debugging but not critical. Implement after consolidation pipeline is stable.
**When:** After M1 (consolidation pipeline) is complete

### D7. 15+ File Parsers (sist2 Pattern)
**Classification:** DEFER
**Reason:** Cortex currently focuses on code files. Non-code document parsing (PDF, EPUB, XLSX, PPTX, audio, video) is valuable but not critical for daemon mode. Implement when desktop users need document ingestion.
**When:** Phase 6-7 (desktop era, when document ingestion becomes a priority)

### D8. Community Marketplace (AnythingLLM Pattern)
**Classification:** DEFER
**Reason:** Cortex needs a stable plugin system first (AD9). Marketplace is a scaling concern, not a core architecture concern.
**When:** After AD9 (plugin architecture) is complete and there are enough plugins to warrant a marketplace

### D9. Embeddable Widgets (AnythingLLM Pattern)
**Classification:** DEFER
**Reason:** Cortex is local-first. Embedding in external websites contradicts the privacy-first model unless explicitly configured. Low priority.
**When:** Only if Cortex gains a server/cloud deployment mode

### D10. Collector Proxy Pattern (AnythingLLM Pattern)
**Classification:** DEFER
**Reason:** Cortex's indexing is already decoupled (batch + real-time tracks). A separate collector microservice adds complexity without immediate benefit for desktop mode.
**When:** Only if server deployment needs independent ingestion scaling

### D11. Saga Pattern for Episode Sequences
**Classification:** DEFER
**Reason:** Cortex's conversation model is sufficient for now. Saga pattern adds complexity without immediate value.
**When:** When cross-session continuity becomes a priority

### D12. Multi-Hop Graph Traversal (Cypher/BFS)
**Classification:** DEFER
**Reason:** Requires graph DB migration (PostgreSQL → Neo4j or embedded graph). Wait until service abstraction phase.
**When:** Phase 2-3 (service abstraction enables graph DB swap)

---

## REJECT (Wrong fit for Cortex)

### X1. SQLite for History (Mem0 Pattern)
**Classification:** REJECT
**Reason:** Cortex already uses PostgreSQL for all persistence. Adding SQLite for history creates a split-brain storage problem. Use PostgreSQL audit_log table instead.
**Alternative:** PostgreSQL audit_log with partitioned tables

### X2. spaCy for Entity Extraction (Mem0 Pattern)
**Classification:** REJECT
**Reason:** spaCy is a heavy NLP dependency (~500MB model download). Cortex should use LLM-based extraction (already has LLM infrastructure). No need for a separate NLP pipeline.
**Alternative:** LLM-based extraction (AD1)

### X3. Proxy Module / OpenAI-Compatible Chat (Mem0 Pattern)
**Classification:** REJECT
**Reason:** Cortex is not a chat wrapper. It's a local intelligence layer. The proxy pattern adds unnecessary abstraction.
**Alternative:** Direct API integration

### X4. PostHog Telemetry (Mem0 Pattern)
**Classification:** REJECT
**Reason:** Cortex is local-first, privacy-first. External telemetry contradicts the product philosophy.
**Alternative:** Local metrics (Cortex already has RetrievalMetrics)

### X5. Neo4j as Primary Graph DB
**Classification:** REJECT (for now)
**Reason:** Neo4j requires a separate server process, Java runtime, and license considerations. Cortex should use an embedded graph solution (Kuzu or PostgreSQL with graph extensions) for the desktop-first vision.
**Alternative:** Kuzu (embedded) or PostgreSQL (current, with graph query optimization)

### X6. SQLite for Platform Data (AnythingLLM Pattern)
**Classification:** REJECT
**Reason:** Cortex already uses PostgreSQL for all persistence. AnythingLLM uses SQLite+Prisma, which works for their simpler data model. Cortex's PostgreSQL is more capable and already deployed. For desktop mode, consider SQLite ONLY for vector storage (turbovec) and FTS5 search — not for core platform data.
**Alternative:** PostgreSQL (current) for platform data; SQLite for vector/FTS5 in desktop mode

### X7. 35+ LLM Providers (AnythingLLM Pattern)
**Classification:** REJECT (for now)
**Reason:** AnythingLLM supports 35+ providers because it's a commercial product with broad market appeal. Cortex should focus on 4-5 key providers (Ollama, OpenAI, Anthropic, LMStudio, Mock) via a clean abstraction. Users can add more via the plugin system (AD9) without Cortex maintaining them.
**Alternative:** Protocol-based provider interface with community-contributed providers

### X8. Elm-Style Frontend (Open WebUI)
**Classification:** REJECT
**Reason:** Open WebUI uses SvelteKit. Cortex uses Next.js/React. Rebuilding the frontend in a different framework is not worth the effort. Keep Next.js.
**Alternative:** Next.js (current)

### X9. FTS5 as Primary Search (sist2 Pattern)
**Classification:** REJECT (for now)
**Reason:** Cortex already has PostgreSQL fulltext search which is more capable than SQLite FTS5. For desktop mode, FTS5 is attractive (no PostgreSQL needed), but Cortex's hybrid retrieval (vector + fulltext + graph) is too integrated with PostgreSQL to swap easily. Consider FTS5 as an alternative ONLY if desktop mode needs to drop PostgreSQL entirely.
**Alternative:** PostgreSQL fulltext (current); SQLite FTS5 as future desktop option

---

## Batch 4 Recommendations — Agent, Orchestration & Tool Systems

### ADOPT (Batch 4)

### A9. @tool Decorator Pattern (from Strands Tools)
**Classification:** ADOPT
**Source:** Strands Tools `@tool` decorator with auto-generated TOOL_SPEC from type hints + docstrings

Replace Cortex's hand-maintained `TOOL_REGISTRY` dict with a decorator-based pattern:
1. `@tool` wraps a function, auto-generates TOOL_SPEC from Python type hints + docstring
2. Tool registry discovers decorated functions at import time
3. No separate schema definition — the function IS the schema

Adapt for Cortex: Add `policy` parameter to decorator (allow/deny/ask per context). Add `preprocessArgs` hook (from Continue) for input sanitization.

**Implementation:** `backend/app/agents/tools/` directory (reorganize from flat file)
**Effort:** Medium — replaces existing TOOL_REGISTRY
**Impact:** Critical — enables all other tool system improvements

### A10. Context Compaction (from Continue + Odysseus)
**Classification:** ADOPT
**Source:** Continue auto-compaction at 85% context window. Odysseus structured summary format.

Adopt Odysseus's compaction format (superior to Continue's plain summarization):
1. Monitor context usage via token counting
2. At threshold (85%), trigger compaction via lightweight LLM call
3. Structured summary: User Goal → What Was Done → Current State → Pending/Next Steps
4. Replace context with summary + recent messages

**Implementation:** `backend/app/services/context/compaction.py`
**Effort:** Low — prompt engineering + integration
**Impact:** Critical — enables long conversations without context loss

### A11. Tool Policy Composition (from Continue + Odysseus)
**Classification:** ADOPT
**Source:** Continue per-tool ToolPolicy. Odysseus per-turn policy composition (plan mode, guide-only).

Adopt Odysseus's per-turn composition model:
1. Each tool has a `ToolPolicy`: `allow | deny | ask` per context
2. Plan mode: deny all write tools. Guide mode: deny all tools. Default: allow read, ask for write
3. Policy composed from: global defaults + agent-specific overrides + context-specific overrides

**Implementation:** `backend/app/agents/policy.py`
**Effort:** Low — data structure + evaluation
**Impact:** High — replaces HMAC approval tokens with composable policy

### A12. Action Intent Classification (from Odysseus)
**Classification:** ADOPT
**Source:** Odysseus `action_intents.py` — regex-based routing for chat vs agent vs command

Adopt Odysseus's deterministic pre-routing:
1. Classify user input as: chat, agent_request, command, or clarification
2. Route chat directly to LLM (no agent loop). Route agent_request through planning. Route command to CLI handler
3. Simple regex + keyword patterns — no LLM call needed for routing

**Implementation:** `backend/app/services/intent/classifier.py`
**Effort:** Low — regex patterns
**Impact:** Medium — reduces unnecessary agent invocations

### A13. MCP Client Wrapper (from Strands Tools + Continue)
**Classification:** ADOPT
**Source:** Strands `MCPTool` wrapper class. Continue `MCPManagerSingleton`.

Adopt Strands's MCPTool wrapper pattern:
1. `MCPTool` wraps external MCP tools into Cortex's tool interface
2. Tool spec derived from MCP server's tool schema
3. Tool execution delegates to MCP server via stdio or SSE transport
4. `MCPManagerSingleton` handles lifecycle (connect, reconnect, disconnect)

**Implementation:** `backend/app/services/mcp/client.py` + `backend/app/agents/tools/mcp_tool.py`
**Effort:** Medium — transport layer + tool wrapping
**Impact:** High — enables MCP ecosystem interoperability

### ADAPT (Batch 4)

### AD13. Agent Execution Loop Rebuild (from Continue + Strands)
**Classification:** ADAPT
**Source:** Continue single-tool-calling loop. Strands tool execution loop with hooks.

Replace Cortex's fragile Planner→Executor two-agent pattern with a single unified agent loop:
1. Single agent with tool-calling loop (not planner + executor)
2. Tool calls execute inline (not via separate executor agent)
3. Pre/post hooks for tool policy enforcement, logging, state tracking
4. AbortController for cancellation
5. Max iterations with graceful degradation (not hard cutoff)

Adapt for Cortex: Keep the planner concept as a planning tool (not a separate agent). The agent can call `plan_task` tool to create a plan, then execute tools to implement it.

**Implementation:** `backend/app/agents/loop.py` (replaces planner.py + executor.py)
**Effort:** High — core agent system rewrite
**Impact:** Critical — current agent loop is the weakest subsystem

### AD14. Context Provider Architecture (from Continue)
**Classification:** ADAPT
**Source:** Continue `IContextProvider` abstract class with 20+ implementations

Adopt Continue's provider pattern but simplify:
1. `ContextProvider` Protocol: `get_items(query, token_budget) -> list[ContextItem]`
2. Built-in providers: CodebaseSearch, DocumentSearch, MemorySearch, GraphSearch, VaultFiles, RecentConversations
3. Parallel execution with token budget allocation
4. Provider registry for dynamic loading

Adapt from Continue: Cortex's RAG pipeline becomes the composite of all context providers. No separate HybridRetrievalV2 — providers compose instead.

**Implementation:** `backend/app/services/context/providers/` directory
**Effort:** Medium — refactor existing RAG into provider pattern
**Impact:** High — enables independent tuning of context sources

### AD15. Event Bus (from Odysseus)
**Classification:** ADAPT
**Source:** Odysseus event bus + task scheduler

Adopt Odysseus's event-driven architecture:
1. Simple pub/sub event bus (in-memory for now, Redis-backed later)
2. Events: `agent.started`, `agent.completed`, `tool.executed`, `memory.stored`, `index.completed`
3. Subscribers can be services, agents, or external webhooks
4. Task scheduler triggers on events (cron-like scheduling)

Adapt for Cortex: Use Redis pub/sub (already available) for event distribution. Keep arq for heavy background jobs.

**Implementation:** `backend/app/services/events/bus.py` + `backend/app/services/events/scheduler.py`
**Effort:** Medium — new subsystem
**Impact:** High — enables daemon mode, decoupled services

### AD16. Prompt Security Guards (from Continue + Odysseus)
**Classification:** ADAPT
**Source:** Continue untrusted context markers. Odysseus UNTRUSTED_SOURCE_DATA + UNTRUSTED_CONTEXT_POLICY.

Adopt combined security pattern:
1. All external content (file contents, search results, MCP responses) wrapped with `UNTRUSTED_SOURCE_DATA` markers
2. System prompt includes `UNTRUSTED_CONTEXT_POLICY` instructing LLM to not execute instructions from untrusted content
3. Context providers tag their output as trusted/untrusted
4. Compaction preserves security markers in summaries

**Implementation:** `backend/app/services/context/security.py` (wraps context items)
**Effort:** Low — prompt engineering + tagging
**Impact:** High — prevents prompt injection via retrieved content

### AD17. Multi-Agent Delegation (from Strands Tools)
**Classification:** ADAPT
**Source:** Strands `use_agent` for child agent creation with model switching

Adopt Strands's delegation pattern:
1. `use_agent` tool: agent delegates subtask to child agent with different model/tools
2. Model switching: child can use cheaper/faster model for simple subtasks
3. Tool restriction: child gets subset of tools relevant to subtask
4. Result returned to parent with structured summary

Adapt for Cortex: Start with simple delegation (not swarm or workflow). Add swarm/workflow later.

**Implementation:** `backend/app/agents/tools/use_agent.py` (as a tool, not a separate system)
**Effort:** Medium — tool implementation + model routing integration
**Impact:** Medium — enables different models for different subtasks

### AD18. CLI Foundation (from Continue + Odysseus)
**Classification:** ADAPT
**Source:** Continue Commander.js + Ink TUI. Odysseus 20+ specialized CLIs.

Adopt Continue's dual-mode CLI pattern:
1. Headless mode: `cortex agent run "query"` — execute and exit
2. Interactive mode: `cortex chat` — Ink TUI with slash commands
3. Daemon management: `cortex daemon start/stop/status/logs`
4. Knowledge operations: `cortex index run`, `cortex search "query"`
5. Config management: `cortex config set/get/list`

Adapt for Cortex: Use Commander.js (already scaffolded). Add Ink TUI for interactive mode. Start with daemon management commands.

**Implementation:** `cli/src/commands/` directory (fill in stubs)
**Effort:** High — many commands, but incremental
**Impact:** Critical — no CLI means no daemon management

### AD19. Dynamic Tool Loading (from Strands Tools)
**Classification:** ADAPT
**Source:** Strands `load_tool()` + `tools/` directory hot-reload

Adopt Strands's dynamic tool loading pattern:
1. Built-in tools registered at startup via @tool decorator
2. User tools discovered from `~/.cortex/tools/` directory
3. `load_tool(path)` loads arbitrary tool at runtime
4. Tool validation: verify tool spec, check for conflicts, sandbox execution

Adapt for Cortex: Use plugin system (AD9) for tool loading. MCP tools load via MCPTool wrapper (A13).

**Implementation:** `backend/app/agents/tools/loader.py`
**Effort:** Medium — loader + validation
**Impact:** Medium — enables user-extensible tools

### AD20. Agent Run Persistence (from Odysseus)
**Classification:** ADAPT
**Source:** Odysseus background jobs with PID tracking + restart-safety

Adopt Odysseus's persistence pattern:
1. Agent runs stored in PostgreSQL with full state (not just results)
2. Steps recorded individually with tool calls, results, and timestamps
3. PID tracking for background runs — detect orphaned processes
4. Restart-safety: resume from last completed step, not from beginning

Adapt for Cortex: Use existing AgentRun/AgentStep models. Add PID tracking and orphan detection. Add resume capability.

**Implementation:** `backend/app/agents/runner.py` (replaces background.py)
**Effort:** Medium — persistence layer + orphan detection
**Impact:** High — enables reliable daemon-mode agent execution

### REPLACE (Batch 4)

### R5. Agent System → Unified Agent Loop (from Continue + Strands)
**Classification:** REPLACE
**Source:** Continue tool-calling loop. Strands tool execution with hooks.

**Replace:** Cortex's Planner→Executor two-agent pattern
**With:** Single unified agent loop with tool-calling, policy enforcement, context compaction, and abort support

The current pattern (planner creates plan, executor implements plan) adds latency and complexity without benefit. A single agent with good tools and a planning tool achieves the same result more reliably.

**Implementation:** `backend/app/agents/loop.py`
**Effort:** High — core system rewrite
**Impact:** Critical — current agent system is the weakest subsystem

### R6. Background Tasks → Event-Driven Runner (from Odysseus)
**Classification:** REPLACE
**Source:** Odysseus background jobs with PID tracking + event triggers

**Replace:** Cortex's in-process asyncio tasks (lost on restart)
**With:** Event-driven runner with persistence, PID tracking, and restart-safety

**Implementation:** `backend/app/services/runner/` directory
**Effort:** High — replaces `background.py` entirely
**Impact:** High — daemon mode requires reliable background execution

### R7. Tool Registry → Decorator-Based Registry (from Strands + Continue)
**Classification:** REPLACE
**Source:** Strands @tool decorator. Continue Tool type with policy hooks.

**Replace:** Cortex's hand-maintained `TOOL_REGISTRY` dict with 9 hardcoded tools
**With:** @tool decorator-based registry with auto-schema, policy hooks, and dynamic loading

**Implementation:** `backend/app/agents/tools/` directory
**Effort:** Medium — replaces `tools.py` and `background.py` tool handling
**Impact:** Critical — foundation for all tool system improvements

### DEFER (Batch 4)

### D13. Swarm Coordination (from Strands Tools)
**Classification:** DEFER
**Source:** Strands swarm with auto-handoff + repetitive behavior detection

Defer swarm pattern until multi-agent delegation (AD17) is stable. Swarm adds decentralized handoff and repetitive behavior detection — valuable for complex multi-step workflows but premature now.

**When:** After AD17 + event bus (AD15)

### D14. Workflow DAG Execution (from Strands Tools)
**Classification:** DEFER
**Source:** Strands workflow with ThreadPoolExecutor + JSON state persistence

Defer DAG execution until basic agent loop (AD13) and event bus (AD15) are stable. Workflow DAG is powerful but complex — start with simple sequential delegation, add DAG when needed.

**When:** After AD13 + AD15

### D15. Ink TUI (from Continue CLI)
**Classification:** DEFER
**Source:** Continue Ink-based TUI with slash commands, sessions, keyboard shortcuts

Defer Ink TUI until headless CLI (AD18) is working. Start with plain Commander.js output, add TUI later for interactive use.

**When:** After AD18 headless CLI is complete

### D16. Deep Research Tool (from Continue)
**Classification:** DEFER
**Source:** Continue deep research tool (multi-step web research)

Defer deep research tool until basic tool system (A9) and agent loop (AD13) are stable. Complex multi-step tool — not a foundation piece.

**When:** After AD13

### D17. Full Audit Trail for Agent Runs (from Odysseus)
**Classification:** DEFER
**Source:** Odysseus comprehensive agent run logging

Defer full audit trail until agent run persistence (AD20) is complete. Start with basic step recording, add comprehensive audit later.

**When:** After AD20

### REJECT (Batch 4)

### X10. XML Tool Invocation Format (from Odysseus)
**Classification:** REJECT
**Source:** Odysseus XML tool invocation parsing

Reject XML tool invocation. LLM providers have standardized on function-calling format. Adding XML parsing adds complexity for no benefit.

### X11. Markdown Tool Invocation Format (from Odysseus)
**Classification:** REJECT
**Source:** Odysseus markdown tool invocation parsing

Reject markdown tool invocation. Same reasoning as X10. Stick with function-calling format.

### X12. Cron-Like Task Scheduler (from Odysseus)
**Classification:** REJECT
**Source:** Odysseus task scheduler with cron expressions

Reject custom cron scheduler. Use arq's built-in scheduling for background jobs. Custom schedulers add operational complexity and failure modes.

---

## Summary: Priority-Ordered Recommendations (All 4 Batches)

### Critical — Do First

| Priority | ID | Classification | Source | Impact | Effort | Phase |
|----------|-----|---------------|--------|--------|--------|-------|
| 1 | R5 | REPLACE | Batch 4 (Continue + Strands) | Agent system → unified agent loop | High | Phase 2 |
| 2 | R7 | REPLACE | Batch 4 (Strands + Continue) | Tool registry → decorator-based | Medium | Phase 2 |
| 3 | A9 | ADOPT | Batch 4 (Strands) | @tool decorator pattern | Medium | Phase 2 |
| 4 | A10 | ADOPT | Batch 4 (Continue + Odysseus) | Context compaction | Low | Phase 2-3 |
| 5 | AD9 | ADAPT | Batch 3 (Open WebUI + AnythingLLM) | Plugin architecture, 3 layers | High | Phase 2-3 |
| 6 | R4 | REPLACE | Batch 3 (AnythingLLM + LlamaIndex + turbovec) | Vector store abstraction | High | Phase 2 + Phase 6 |
| 7 | M1 | MERGE | Batch 1 (Mem0 + Graphiti + Cortex) | Memory consolidation pipeline | High | Parallel to Phase 2-3 |
| 8 | R3 | REPLACE | Batch 3 (AnythingLLM + LlamaIndex) | Embedding provider abstraction | Medium | Phase 2 |
| 9 | AD16 | ADAPT | Batch 4 (Continue + Odysseus) | Prompt security guards | Low | Phase 2 |
| 10 | A11 | ADOPT | Batch 4 (Continue + Odysseus) | Tool policy composition | Low | Phase 2 |

### Important — Do After Critical

| Priority | ID | Classification | Source | Impact | Effort | Phase |
|----------|-----|---------------|--------|--------|--------|-------|
| 11 | AD13 | ADAPT | Batch 4 (Continue + Strands) | Agent execution loop rebuild | High | Phase 2-3 |
| 12 | R6 | REPLACE | Batch 4 (Odysseus) | Background tasks → event-driven runner | High | Phase 3 |
| 13 | AD18 | ADAPT | Batch 4 (Continue + Odysseus) | CLI foundation | High | Phase 4 |
| 14 | AD15 | ADAPT | Batch 4 (Odysseus) | Event bus | Medium | Phase 3 |
| 15 | AD14 | ADAPT | Batch 4 (Continue) | Context provider architecture | Medium | Phase 2-3 |
| 16 | AD11 | ADAPT | Batch 3 (AnythingLLM) | MCP integration | High | Phase 3 |
| 17 | AD20 | ADAPT | Batch 4 (Odysseus) | Agent run persistence | Medium | Phase 3 |
| 18 | AD17 | ADAPT | Batch 4 (Strands) | Multi-agent delegation | Medium | Phase 3 |
| 19 | AD8 | ADAPT | Batch 3 (AnythingLLM) | Model routing | Medium | After Phase 2 |
| 20 | A7 | ADOPT | Batch 3 (Open WebUI) | PersistentConfig pattern | Medium | Phase 2 or 5 |
| 21 | A1 | ADOPT | Batch 1 (Mem0) | Memory dedup pipeline | Medium | Parallel to Phase 2-3 |
| 22 | AD1 | ADAPT | Batch 1 (Graphiti) | LLM-based entity extraction | Medium | Parallel to Phase 2-3 |
| 23 | A8 | ADOPT | Batch 3 (Open WebUI + AnythingLLM) | OpenAI-compatible API | Medium | Phase 5 |
| 24 | A12 | ADOPT | Batch 4 (Odysseus) | Action intent classification | Low | Phase 3 |
| 25 | A13 | ADOPT | Batch 4 (Strands + Continue) | MCP client wrapper | Medium | Phase 3 |
| 26 | AD19 | ADAPT | Batch 4 (Strands) | Dynamic tool loading | Medium | Phase 3 |
| 27 | M2 | MERGE | Batch 1 + Batch 2 | Hybrid search pipeline | High | After M1 |
| 28 | R1 | REPLACE | Batch 1 (Graphiti) | LLM-based graph builder | High | After M1 |
| 29 | AD6 | ADAPT | Batch 2 (LlamaIndex) | Hierarchical chunking | Medium | After Phase 2 |
| 30 | AD10 | ADAPT | Batch 3 (AnythingLLM) | Vault settings | Medium | Phase 5 |
| 31 | AD7 | ADAPT | Batch 2 (sist2) | Two-phase scan/index | Medium | Phase 2-3 |
| 32 | A5 | ADOPT | Batch 2 (LlamaIndex) | IngestionCache | Medium | After Phase 2 |
| 33 | A6 | ADOPT | Batch 1+2 (Mem0 + LlamaIndex) | BM25 sigmoid + fusion modes | Low | After M1 |
| 34 | AD2 | ADAPT | Batch 1 (Graphiti) | Composable search recipes | Medium | After M2 |
| 35 | AD3 | ADAPT | Batch 1 (Mem0) | Entity boosting | Medium | After M2 |
| 36 | AD4 | ADAPT | Batch 1 (Graphiti) | MMR diversity reranking | Low | After M2 |
| 37 | AD5 | ADAPT | Batch 1 (Graphiti) | Bi-temporal knowledge | Low | After M1 |
| 38 | M3 | MERGE | Batch 1 (Mem0 + Graphiti + Cortex) | Entity model | Medium | After M1 |
| 39 | R2 | REPLACE | Batch 1 (Mem0) | Adaptive score normalization | Low | After M2 |
| 40 | AD12 | ADAPT | Batch 2 (turbovec) | Scalar quantization for desktop | High | Phase 6 |
| 41 | A2 | ADOPT | Batch 1 (Mem0) | Triple-signal scoring | Low | After M1 |
| 42 | A3 | ADOPT | Batch 1 (Mem0) | BM25 sigmoid | Low | After M1 |

### Deferred

| Priority | ID | Classification | Source | Reason | When |
|----------|-----|---------------|--------|--------|------|
| 43 | D1 | DEFER | Batch 1 | Cross-encoder reranking (GPU needed) | Phase 6-7 |
| 44 | D2 | DEFER | Batch 1 | Community detection (needs richer graph) | After M3 |
| 45 | D7 | DEFER | Batch 2 | 15+ file parsers (non-code docs) | Phase 6-7 |
| 46 | D8 | DEFER | Batch 3 | Community marketplace (needs plugin system first) | After AD9 |
| 47 | D9 | DEFER | Batch 3 | Embeddable widgets (contradicts local-first) | If cloud mode |
| 48 | D10 | DEFER | Batch 3 | Collector proxy (unnecessary for desktop) | If server scaling |
| 49 | D11 | DEFER | Batch 1 | Saga pattern (needs cross-session priority) | Future |
| 50 | D12 | DEFER | Batch 1 | Multi-Hop graph traversal (needs graph DB swap) | Phase 2-3 |
| 51 | D4 | DEFER | Batch 1 | Multi-hop traversal with Cypher | Phase 2-3 |
| 52 | D5 | DEFER | Batch 1 | Action-aware embeddings | Phase 2 |
| 53 | D6 | DEFER | Batch 1 | Full audit trail | After M1 |
| 54 | D13 | DEFER | Batch 4 | Swarm coordination (needs AD17 first) | After AD17 + AD15 |
| 55 | D14 | DEFER | Batch 4 | Workflow DAG execution (needs AD13 + AD15) | After AD13 + AD15 |
| 56 | D15 | DEFER | Batch 4 | Ink TUI (needs AD18 first) | After AD18 |
| 57 | D16 | DEFER | Batch 4 | Deep research tool (needs AD13 first) | After AD13 |
| 58 | D17 | DEFER | Batch 4 | Full audit trail for agent runs (needs AD20) | After AD20 |

### Rejected

| ID | Classification | Source | Reason |
|----|---------------|--------|--------|
| X1 | REJECT | Batch 1 | SQLite for history (use PostgreSQL audit_log) |
| X2 | REJECT | Batch 1 | spaCy for NER (use LLM extraction) |
| X3 | REJECT | Batch 1 | Proxy module (Cortex is not a chat wrapper) |
| X4 | REJECT | Batch 1 | PostHog telemetry (privacy-first) |
| X5 | REJECT | Batch 1 | Neo4j as primary graph DB (use Kuzu or PostgreSQL) |
| X6 | REJECT | Batch 3 | SQLite for platform data (keep PostgreSQL) |
| X7 | REJECT | Batch 3 | 35+ LLM providers (focus on 4-5 via Protocol) |
| X8 | REJECT | Batch 3 | Elm-style frontend (keep Next.js) |
| X9 | REJECT | Batch 3 | FTS5 as primary search (keep PostgreSQL fulltext) |
| X10 | REJECT | Batch 4 | XML tool invocation format (use function-calling) |
| X11 | REJECT | Batch 4 | Markdown tool invocation format (use function-calling) |
| X12 | REJECT | Batch 4 | Cron-like task scheduler (use arq) |

### Classification Counts

| Classification | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Total |
|---------------|---------|---------|---------|---------|-------|
| **ADOPT** | 4 | 2 (+ A6 merged) | 2 | 5 | **13** |
| **ADAPT** | 5 | 3 | 4 | 8 | **20** |
| **MERGE** | 3 | 0 | 0 | 0 | **3** |
| **REPLACE** | 2 | 0 (+ R3, R4) | 2 | 3 | **7** |
| **DEFER** | 6 | 1 | 5 | 5 | **17** |
| **REJECT** | 5 | 0 (+ X9) | 4 | 3 | **12** |
| **Total** | 25 | 6 | 13 | 24 | **72** |
