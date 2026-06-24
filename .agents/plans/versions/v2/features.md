# CORTEX V2: "The Architecture"

**Version:** 2
**Date:** 2026-06-25
**Status:** Planned

---

## 1. Goals

V2 transforms CORTEX from a monolithic backend into an extensible, decoupled architecture. Services gain clean interfaces. Components communicate through events. External tools integrate via MCP. The plugin system opens the platform to community contribution.

This is the architectural version — the one where the codebase aligns with the constitution's principles of separation of concerns, plugin boundaries early, and graceful degradation through swappable implementations.

### Primary Goals

1. **Service abstraction** — Every major service has a Protocol interface. Implementations are swappable. LLM, embedding, vector store, cache — all behind clean boundaries.
2. **Event bus** — In-process pub/sub decouples services. Observable with tracing. No external dependency.
3. **MCP integration** — Full MCP client. External tools appear as native Cortex tools. Stdio + SSE transports.
4. **Plugin system** — Three-layer architecture (providers, tools, pipelines). Protocol interfaces. Decorator registration.
5. **Memory consolidation** — LLM-based extraction, 3-level dedup, contradiction detection, bi-temporal tracking.

### Non-Goals (Explicitly Deferred)

- CLI additions beyond V1 (V3 adds Unix socket, TUI)
- Desktop shell / Tauri (V3)
- Embedded databases (V3)
- Task scheduler / automation (V4)
- Daily productivity tools (V5)
- MCP server (expose Cortex tools to others) (V4)
- Ecosystem features (V6)

---

## 2. Scope

### 2.1 Service Abstraction Layer

| Service | Current State | V2 State |
|---------|--------------|----------|
| LLM | `llm/manager.py` — hardcoded routing to Ollama/llama.cpp/mock | `Protocol[LLMProvider]` with factory registration. Ollama + llama.cpp + mock as implementations. |
| Embedding | `embedding_service.py` — three-tier if/elif chain | `Protocol[EmbeddingProvider]` with registry. ONNX + Ollama + mock as implementations. |
| Vector store | `core/vector_db.py` — direct Qdrant calls | `Protocol[VectorStore]` with factory. Qdrant as server-mode implementation. In-memory as fallback. Desktop implementation deferred to V3. |
| Cache | `core/redis.py` — Redis with in-memory fallback | `Protocol[CacheProvider]`. Redis + in-memory LRU as implementations. |
| Database | SQLAlchemy engine — PostgreSQL | `Protocol[DatabaseProvider]`. PostgreSQL as implementation. Embedded PostgreSQL benchmarked. |

**Design constraint:** Protocol interfaces are Python structural subtyping (typing.Protocol), not ABC inheritance. Implementations register via decorator. First implementation ships behind the interface — behavior is identical before and after.

**Scope boundary:** The abstraction layer does NOT change any service behavior. It wraps existing implementations behind interfaces. New implementations (embedded Qdrant, alternative LLMs) are possible but not required in V2.

### 2.2 Event Bus

| Aspect | V2 Design |
|--------|----------|
| Architecture | In-process pub/sub. No external dependency (no Redis pub/sub, no external message broker). |
| Events | Typed: `file_changed`, `memory_decayed`, `index_complete`, `entity_discovered`, `conversation_archived`, `agent_run_complete`, `job_started`, `job_completed`, `job_failed` |
| Subscribers | Services register interest in event types. Callbacks are async. |
| Observability | Every event traced with metadata (timestamp, source, duration). Event log table in PostgreSQL. |
| Ordering | Within a single producer, events are ordered. Cross-producer ordering is not guaranteed. |
| Delivery | At-least-once. Subscribers must be idempotent. |
| Scope | Internal only. No external event sources or sinks in V2. |

**Design constraint:** The event bus is in-process. It replaces direct service imports with typed events. It does NOT introduce Redis pub/sub, Kafka, or any external dependency.

**What changes:** Services that currently import each other's modules communicate through events instead. The agent publishes `agent_run_complete`. The memory service subscribes and extracts facts. The graph service subscribes and extracts entities. No direct imports between these services.

### 2.3 MCP Integration

| Component | V2 Design |
|-----------|----------|
| MCP client | Full manager. Stdio + SSE transports. Lifecycle management (start, stop, restart, health). |
| MCP server | Defer to V4. Not in V2. |
| Tool wrapping | External MCP tools appear as native Cortex tools via MCPTool wrapper. |
| Server registry | Database-backed. Users register MCP servers via CLI or API. |
| Discovery | Registered MCP servers are scanned for available tools on startup. |
| Error handling | Failed MCP servers degrade gracefully. Other tools remain available. |

**Scope boundary:** V2 is MCP client only. Cortex consumes external tools. It does NOT expose its own tools via MCP (that's V4). This keeps the scope manageable.

### 2.4 Plugin System

| Layer | Purpose | V2 Implementation |
|-------|---------|-------------------|
| Layer 1: Providers | LLM, embedding, vector store | Protocol interfaces + factory registration (part of 2.1) |
| Layer 2: Tools | Agent tools | @tool decorator + MCP tool wrapping (part of V1 agent rebuild + MCP) |
| Layer 3: Pipelines | Processing chains | Composable pipeline stages for indexing, consolidation, retrieval |

| Aspect | V2 Design |
|--------|----------|
| Interface | Python Protocol (structural subtyping) |
| Registration | `@register_provider("llm", "ollama")` decorator pattern |
| Discovery | Filesystem scan of `~/.cortex/plugins/` |
| Loading | Lazy — loaded on first use, not at startup |
| Versioning | Plugin API versioned. Breaking changes require major version bump. |
| Documentation | Plugin authoring guide with examples |

**Scope boundary:** V2 defines the plugin interfaces and ships the first implementations behind them. The community plugin ecosystem is a V4+ concern.

### 2.5 Memory Consolidation Pipeline

| Stage | V2 Implementation | Source |
|-------|-------------------|--------|
| Extraction | LLM-based fact extraction from conversations, documents, code | Graphiti pattern |
| Dedup (batch) | Within-extraction dedup via embedding similarity | Mem0 V3 |
| Dedup (existing) | Compare new facts against existing memories via vector similarity | Mem0 V3 |
| Dedup (exact) | Hash-based exact match | Mem0 V3 |
| Contradiction | When new fact contradicts existing, invalidate old with `invalid_at` | Graphiti pattern |
| Merge | Consolidate duplicate memories, keep highest confidence | Custom |
| Confidence | Assign initial confidence, apply decay formula (keep Cortex's 0.95x/30d) | Cortex existing |
| Bi-temporal | Add `valid_at`/`invalid_at` to LongTermMemory | Graphiti pattern |

**Scope boundary:** The pipeline runs as a background job triggered by the event bus. When new content is indexed or a conversation is archived, the pipeline extracts, deduplicates, and consolidates. It does NOT run on every user message.

**What changes:** Memory goes from "stores facts manually" to "understands, consolidates, and maintains facts automatically."

### 2.6 LLM-Based Entity Extraction

| Aspect | V2 Design |
|--------|----------|
| Current | Regex-based extraction (entity_extractor.py, 220 lines) |
| V2 | LLM-based extraction for code AND non-code content |
| Scope | Code (import/call/inheritance + new relationships), conversations, documents |
| Pipeline | Runs as background job via event bus (when content is indexed) |
| Graph update | Extracted entities and relationships update GraphNode/GraphEdge |

**Scope boundary:** LLM-based extraction replaces regex. It runs as a background job, not inline with user requests. Graph quality improves incrementally.

### 2.7 Context Provider Architecture

| Aspect | V2 Design |
|--------|----------|
| Pattern | Continue's IContextProvider — composable, token-budgeted sources |
| Providers | Memory provider, graph provider, search provider, vault provider, conversation provider |
| Budget | Each provider gets a token budget. Sources compete for budget based on relevance. |
| Compaction | Auto-compaction uses providers to build structured summary |
| Domain rules | Tool-to-domain mapping for context injection |

**Scope boundary:** Context providers replace the monolithic hybrid_retrieval.py pipeline. Each provider is independent and composable. The agent loop consumes providers, not a single pipeline.

### 2.8 Additional V2 Capabilities

| Capability | Why |
|-----------|-----|
| PersistentConfig | Env → DB → User config hierarchy (Open WebUI pattern) |
| Model routing | Right model for right task (AnythingLLM pattern) |
| Retrieval enhancements | Adaptive score normalization, entity boosting, composable search recipes |
| API deprecation policy | Documented: one major version notice before removal |
| Plugin authoring guide | How to write plugins for each layer |

---

## 3. Success Criteria

### Functional

| Criterion | Measure |
|-----------|---------|
| Service abstraction | All 5 services (LLM, embedding, vector store, cache, database) behind Protocol interfaces |
| Swappable | New LLM provider can be registered without modifying core code |
| Event bus | Services communicate via events. No direct imports between agent, memory, graph. |
| MCP client | External MCP tools appear as native Cortex tools |
| Plugin system | Plugin author can add a provider or tool by implementing a Protocol + decorator |
| Memory consolidation | Automated pipeline extracts, deduplicates, and consolidates memories |
| LLM extraction | Entity extraction quality improves (measured by graph query precision) |
| Context providers | Agent context is composable and token-budgeted |
| Zero regression | All V1 tests pass. Web UI unchanged. API backward compatible. |

### Quality

| Criterion | Measure |
|-----------|---------|
| Test count | V1 count + new tests for abstraction, event bus, MCP, plugins, consolidation |
| Lint | `make lint` passes |
| Plugin guide | Author can create a plugin using only the documentation |
| Event tracing | Every event observable with metadata |
| API versioning | `/api/v1/` backward compatibility verified |

---

## 4. User Impact

### Before V2

- Adding a new LLM provider requires modifying `llm/manager.py`
- Adding a new embedding provider requires modifying `embedding_service.py`
- Services are tightly coupled through imports
- Memory accumulates duplicates and contradictions without detection
- No external tool integration
- No community contribution path

### After V2

- Adding a new LLM provider = implement Protocol + register decorator
- Adding a new embedding provider = implement Protocol + register decorator
- Services communicate through events, independently testable
- Memory consolidates automatically: dedup, contradiction detection, confidence decay
- External MCP tools work natively within Cortex
- Community can add providers, tools, and pipelines without forking

### Who Benefits

| User | How |
|------|-----|
| Plugin authors | Clean Protocol interfaces, documented plugin guide |
| Power users | MCP integration brings external tools |
| Memory users | Automatic consolidation, no more duplicates |
| Developers | Decoupled services, easier to test and modify |

---

## 5. Architecture Impact

### What Changes

```
V1:
  Agent → imports → Memory, Graph, Search, LLM, Embedding
  (tight coupling through direct imports)

V2:
  Agent → events → Event Bus → Memory, Graph, Search
  Agent → Protocol → LLM Provider, Embedding Provider
  MCP Tools → MCPTool wrapper → Agent
  Plugin Registry → Protocol implementations → Services
```

### Service Boundary Map (After V2)

```
┌──────────────────────────────────────────────────┐
│                 PLUGIN LAYER                      │
│  @register_provider  @tool  Pipeline stages      │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│              PROTOCOL LAYER                       │
│  LLMProvider  EmbeddingProvider  VectorStore     │
│  CacheProvider  DatabaseProvider                  │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│              EVENT BUS                            │
│  file_changed  memory_decayed  index_complete    │
│  entity_discovered  agent_run_complete            │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│           SERVICE BOUNDARIES                      │
│  Memory  │  Graph  │  Retrieval  │  Agent        │
│  Index   │  Embed  │  LLM        │  Search       │
└──────────────────────────────────────────────────┘
```

### What Stays

| Component | Why |
|-----------|-----|
| FastAPI backend | Still the daemon kernel |
| PostgreSQL 16 | Still the primary database |
| All existing services | Wrapped behind interfaces, behavior unchanged |
| Agent loop (V1 rebuild) | Single streaming loop, now consuming Protocol interfaces |
| CLI (V1 completion) | All 15 commands, unchanged |
| Hybrid retrieval | Enhanced but same architecture (RRF + MMR) |
| 341+ tests | The safety net |

---

## 6. UX Impact

### Surfaces

| Surface | V2 Change |
|---------|-----------|
| Web UI | No change for existing features. New: plugin management page (settings). |
| CLI | New commands: `cortex plugin list/install/remove`, `cortex mcp list/connect` |
| API | New endpoints: plugin management, MCP server management, memory consolidation status |
| Desktop shell | Not in V2 (V3) |

### Interaction Model

| Before V2 | After V2 |
|-----------|----------|
| Memory fills with duplicates | Memory consolidates automatically |
| External tools unavailable | MCP tools appear as native Cortex tools |
| Adding providers = forking code | Adding providers = implementing Protocol |
| Services tightly coupled | Services independently testable |

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Service abstraction adds overhead | Low | Medium | Protocol interfaces are thin wrappers. No behavior change. |
| Event bus introduces subtle bugs | Medium | High | Idempotent subscribers. Event tracing. Integration tests. |
| MCP ecosystem instability | Medium | Medium | MCP client only (not server). Graceful degradation on MCP failures. |
| Plugin interface instability | Medium | High | Lock Protocol interfaces before opening to community. Version the API. |
| Memory consolidation quality | Medium | High | Start with extraction only. Add dedup in second pass. Validate against real conversations. |
| LLM extraction cost | Medium | Medium | Use cheaper model for extraction. Batch processing. Background jobs only. |
| Context provider regression | Medium | High | Feature flag for new vs old retrieval. A/B test with existing search quality. |

---

## 8. Exit Criteria (V2 Complete When)

- [ ] 5 Protocol interfaces defined (LLM, Embedding, VectorStore, Cache, Database)
- [ ] Existing implementations moved behind interfaces
- [ ] New provider can be registered without modifying core code
- [ ] Event bus operational with typed events
- [ ] Services communicate via events (no direct imports between boundaries)
- [ ] MCP client connects to external servers, wraps tools as native
- [ ] Plugin system: 3 layers defined, first implementations registered
- [ ] Plugin authoring guide published
- [ ] Memory consolidation pipeline runs as background job
- [ ] LLM-based entity extraction replaces regex
- [ ] Context provider architecture operational
- [ ] PersistentConfig pattern implemented
- [ ] Model routing operational
- [ ] All V1 tests pass
- [ ] New tests for abstraction, events, MCP, plugins, consolidation
- [ ] API backward compatibility verified
- [ ] `make lint` + `make format` clean
