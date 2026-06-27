# v1.07: Memory Evolution — CORTEX

**Document:** Version 1.07 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Capability Delivery

---

## Objective

Evolve memory system with graph structure, consolidation, cross-domain connections, temporal awareness, and evolution tracking. Transform flat memory storage into a living, self-organizing knowledge graph where memories strengthen, decay, merge, and connect across domains — mimicking how human memory consolidates during sleep and strengthens with recall.

---

## Question

"Can Cortex's memory grow and evolve?"

---

## What This Version Delivers

After completing v1.07, Cortex's memory can:

- **Graph Structure** — Represent memories as nodes in a knowledge graph with typed, weighted edges. Each memory type (episodic, semantic, working) becomes a node; relationships (caused_by, related_to, part_of, contradicts, supports) become edges. Enables path-finding, community detection, and centrality analysis.
- **Memory Consolidation** — Merge similar episodic memories into consolidated semantic knowledge. Extract themes from clusters of related memories. Apply LLM-based two-phase extraction (per Architecture Principle 4.3) to distill raw experiences into reusable knowledge.
- **Cross-Domain Connections** — Link memories across different Cortex subsystems (code, email, calendar, documents) into a unified graph. A commit message can connect to the email that prompted it, the calendar event where it was discussed, and the document it modified.
- **Temporal Awareness** — Track when memories occurred, when they were last accessed, and how they relate to each other chronologically. Bi-temporal tracking with `valid_at`/`invalid_at` timestamps per Architecture Principle 4.3. Detect temporal patterns in memory creation (daily bursts, weekly cycles).
- **Memory Evolution** — Memories gain and lose confidence over time. Accessed memories strengthen (access-count reinforcement). Unused memories decay (0.95x per 30-day cycle per Architecture Principle 4.3). Contradicted memories get `invalid_at` timestamps. Memory reflection generates meta-insights about memory patterns.
- **Memory Reflection** — Periodic self-analysis of memory state. Identify most-connected nodes, orphan memories, high-centrality knowledge hubs. Generate insights about what Cortex knows well vs. what it knows poorly.

---

## Capabilities Delivered

| ID | Name | Domain | Priority | Architecture Principle |
|----|------|--------|----------|----------------------|
| M3 | Graph Structure | Memory | Core | 4.4 (Graph Architecture) — explicit service boundary |
| M5 | Memory Consolidation | Memory | Core | 4.3 (Memory Architecture) — LLM-based two-phase extraction |
| M8 | Cross-Domain Connections | Memory | Core | 4.5 (Retrieval Architecture) — graph results feed into RRF |
| M9 | Temporal Awareness | Memory | Core | 4.3 (Memory Architecture) — bi-temporal `valid_at`/`invalid_at` |
| M11 | Memory Evolution | Memory | Core | 4.3 (Memory Architecture) — confidence decay + reinforcement |
| M13 | Memory Reflection | Memory | Core | 3.7 (Incremental Safety) — meta-cognition for self-assessment |

**Total: 6 capabilities**

---

## reference architecture Feature Traceability

| reference architecture Feature | Cortex Mapping | v1.07 Coverage |
|-----------------|----------------|----------------|
| Persistent memory graph | M3 (Graph Structure) | Full — node/edge models, traversal |
| Memory consolidation on idle | M5 (Memory Consolidation) | Full — merge similar, extract themes |
| Contradiction detection via `invalid_at` | M11 (Memory Evolution) | Full — evolutionary weakening |
| Bi-temporal memory tracking | M9 (Temporal Awareness) | Full — valid_at/invalid_at timestamps |
| Graph-enhanced retrieval | M8 (Cross-Domain Connections) | Full — edges feed RRF |
| Access-count reinforcement | M11 (Memory Evolution) | Full — confidence boost on recall |

**reference architecture coverage for this version: 6 features, all fully covered.**

---

## Capability Mapping

```
v1.07 Memory Evolution
├── P01: Memory Graph Models (M3)
│   ├── MemoryNode model (episodic/semantic/working → graph node)
│   ├── MemoryEdge model (typed, weighted relationships)
│   ├── Graph Pydantic schemas (node/edge/graph response)
│   └── Alembic migration (memory_nodes, memory_edges tables)
├── P02: Consolidation & Evolution (M5, M11, M13)
│   ├── MemoryConsolidationService (merge similar episodic → semantic)
│   ├── MemoryEvolutionService (strengthen, decay, invalidate)
│   ├── MemoryReflectionService (meta-analysis, insight generation)
│   └── Graph construction from existing memories
├── P03: Cross-Domain & Temporal (M8, M9)
│   ├── CrossDomainService (link memories across subsystems)
│   ├── TemporalAwarenessService (time-range queries, pattern detection)
│   ├── Graph traversal (BFS/shortest-path, community detection)
│   └── Temporal pattern analysis (gap analysis, burst detection)
└── P04: API & Integration (all)
    ├── Memory graph API endpoints (graph, consolidate, evolve, temporal)
    ├── Graph visualization frontend hooks
    ├── Comprehensive test suite
    └── Frontend API client (features/memory/api.ts)
```

---

## Strengthened Definition of Done

- [ ] All 6 memory evolution capabilities implemented and tested
- [ ] `MemoryNode` and `MemoryEdge` models with proper indexes (user_id, memory_type, source/target_node_id)
- [ ] Alembic migration applies cleanly on fresh DB and on existing DB with v1.03 data
- [ ] Migration rollback tested: downgrade removes graph tables, upgrade restores them
- [ ] `MemoryConsolidationService` merges memories with Jaccard similarity > 0.8 threshold
- [ ] `MemoryEvolutionService` applies daily decay (0.01 rate) and access-count reinforcement (+0.1 per recall)
- [ ] `CrossDomainService` links memories across episodic/semantic/working types
- [ ] `TemporalAwarenessService` handles time-range queries and detects temporal patterns
- [ ] Graph traversal finds shortest paths between any two nodes
- [ ] All API endpoints have `response_model=` decorators per Architecture Principle 1.10
- [ ] Ownership checks: `resource.user_id == current_user.id` on ALL user-scoped endpoints
- [ ] Frontend API client typed with TypeScript interfaces matching Pydantic schemas
- [ ] All existing tests pass (zero regression)
- [ ] New test coverage ≥ 80% for all new services
- [ ] `make lint` + `make format` clean
- [ ] `make hooks-merge` passes

---

## Expanded Risk Matrix

| Risk | Likelihood | Impact | Mitigation | Phase |
|------|-----------|--------|------------|-------|
| Graph table migration fails on large existing datasets | Medium | High | Batch migration with progress logging; test on DB with 10k+ memories | P01 |
| Consolidation merges unrelated memories (false positive similarity) | Medium | Medium | Conservative 0.8 threshold; human review API for edge cases; A/B test threshold values | P02 |
| Memory decay over-aggressively prunes important memories | Low | High | Min confidence floor of 0.1; access-count reinforcement counterbalances; decay rate configurable per user | P02 |
| Cross-domain links create circular references causing infinite traversal | Low | High | Max traversal depth of 10; cycle detection via visited-set in BFS | P03 |
| Temporal queries on large datasets cause performance degradation | Medium | Medium | Composite index on (user_id, created_at); limit default results to 100; pagination support | P03 |
| Graph visualization frontend causes memory leaks with large graphs | Medium | Low | Lazy loading; max 500 visible nodes; virtual scrolling in graph renderer | P04 |
| Consolidation job blocks main event loop | Low | Medium | Run as background task via event bus (Architecture Principle 4.7); yield control periodically | P02 |
| Edge weight accumulation creates misleading strong connections | Medium | Medium | Cap weight at 2.0; periodic normalization pass; weight decay for unaccessed edges | P03 |

---

## Architecture Principle Cross-References

| Principle | How v1.07 Adheres |
|-----------|-------------------|
| **1.1 Local-First** | All graph data stored in PostgreSQL; no external graph DB dependency. Graph operations are pure SQL — no Neo4j, no TigerGraph. |
| **1.2 Graceful Degradation** | If graph tables don't exist (pre-migration), memory services fall back to flat list queries. Consolidation skips if no similar pairs found. |
| **1.3 Daemon-First** | Graph operations run as daemon background tasks via event bus. No blocking on main request loop. |
| **1.4 Separation of Concerns** | Graph is its own service boundary (Architecture Principle 4.4). Memory consolidation is separate from evolution. Cross-domain linking is separate from traversal. |
| **1.5 Plugin Boundaries** | Graph service exposes a clean `GraphServiceProtocol` for potential external graph DB plugins (Neo4j, etc.) in future versions. |
| **1.6 Evidence Over Opinion** | Consolidation threshold (0.8) is data-driven. Decay rates are configurable. All operations log decisions for audit. |
| **1.7 Incremental Safety** | Migration is forward-only with rollback. Each phase is independently testable. Graph features behind feature flag initially. |
| **4.3 Memory Architecture** | Bi-temporal tracking via `valid_at`/`invalid_at`. Confidence decay (0.95x/30d). Three-level deduplication. Graphiti-pattern contradiction detection. |
| **4.4 Graph Architecture** | Explicit service boundary separate from memory. LLM-based entity extraction for edge creation. Temporal valid/invalid timestamps on edges. Graph results feed into hybrid retrieval via RRF. |
| **4.5 Retrieval Architecture** | Graph traversal results feed into RRF (Reciprocal Rank Fusion) alongside vector and fulltext results. MMR diversity reranking prevents graph-dominant results. |
| **4.7 Workflow Architecture** | Consolidation and evolution run as persistent jobs via arq + Redis. Restart survival. Priority queuing for urgent consolidations. |

---

## Downstream Dependency Impact

### Directly Blocked Versions

| Version | What It Needs from v1.07 | Impact if Delayed |
|---------|-------------------------|-------------------|
| **v1.14 (Advanced Intelligence)** | Graph structure for intelligent retrieval, consolidation for knowledge base quality, cross-domain connections for multi-source reasoning | Cannot build advanced reasoning without structured knowledge graph |

### Indirect Dependencies

| Version | Why v1.07 Matters | Workaround |
|---------|-------------------|------------|
| **v1.10 (Planning & Orchestration)** | Uses graph traversal for plan dependency analysis | Manual dependency tracking (brittle) |
| **v1.11 (Interaction)** | Cross-domain connections enable context-aware suggestions | Flat memory search (slower, less accurate) |
| **v1.12 (Developer Tools)** | Graph structure maps code entities and their relationships | Separate code graph (duplication) |
| **v1.13 (Autonomous Agents)** | Memory evolution enables long-running agent knowledge accumulation | Ephemeral agent memory only |

### Integration Points with Other Versions

- **v1.03 (Memory Foundation)** — v1.07 extends the episodic/semantic/working memory models with graph wrappers. No changes to v1.03 models; graph models reference via foreign keys.
- **v1.04 (Awareness Foundation)** — v1.08 awareness events will feed into the graph as nodes. Cross-domain links will connect awareness data to memory data.
- **v1.09 (Learning Foundation)** — User preferences and patterns will be graph nodes. Learning events will be edges connecting user actions to outcomes.
- **v1.02 (Backend Architecture)** — v1.07 services use the established service constructor injection pattern. Graph jobs use the arq + Redis job queue from v1.02.

---

## Phases

| Phase | Name | Focus | Complexity | Duration | Capabilities |
|-------|------|-------|------------|----------|-------------|
| P01 | Memory Graph Models | Graph node/edge models, schemas, migration, rollback | Medium | 2-3 hours | M3 |
| P02 | Consolidation & Evolution | Merge, refine, decay, reflection services | High | 5-6 hours | M5, M11, M13 |
| P03 | Cross-Domain & Temporal | Cross-domain connections, time awareness, graph traversal | High | 5-6 hours | M8, M9 |
| P04 | API & Integration | Endpoints, frontend hooks, graph visualization, tests | Medium | 3-4 hours | All |

**Total estimated: 15-19 hours (2-3 days focused development)**

---

## Dependencies

**Depends on:** v1.03 (Memory Foundation) — needs episodic, semantic, working memory models
**Blocks:** v1.14 (Advanced Intelligence) — needs graph structure for intelligent retrieval

**External dependencies:**
- PostgreSQL 14+ (JSONB support for graph metadata)
- SQLAlchemy 2.0 (async session support for graph queries)
- Alembic (migration management)
- Redis (job queue for background consolidation/evolution tasks)

**Internal dependencies:**
- `backend/app/models/memory/` — existing episodic, semantic, working memory models
- `backend/app/db/session.py` — `get_db()` generator for database sessions
- `backend/app/core/config.py` — configuration for decay rates, thresholds
- `backend/app/auth/dependencies.py` — `get_current_user` for ownership checks
- Event bus from v1.02 for background task dispatch

---

## Estimated Duration

5-6 days (15-19 hours focused development).

---

## Implementation Notes

### Database Schema Additions

```sql
-- P01 migration output
CREATE TABLE memory_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    memory_type VARCHAR(50) NOT NULL,  -- 'episodic', 'semantic', 'working'
    memory_id INTEGER NOT NULL,        -- FK to source memory table
    label VARCHAR(500),
    embedding JSON,                     -- Vector for similarity (768-dim)
    confidence FLOAT DEFAULT 1.0,
    metadata JSON,                      -- Extensible properties
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    UNIQUE(user_id, memory_type, memory_id)
);

CREATE INDEX idx_memory_nodes_user ON memory_nodes(user_id);
CREATE INDEX idx_memory_nodes_type ON memory_nodes(user_id, memory_type);
CREATE INDEX idx_memory_nodes_confidence ON memory_nodes(user_id, confidence);

CREATE TABLE memory_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node_id INTEGER NOT NULL,
    target_node_id INTEGER NOT NULL,
    relationship VARCHAR(100) NOT NULL,  -- 'related_to', 'caused_by', 'part_of', etc.
    weight FLOAT DEFAULT 1.0,
    confidence FLOAT DEFAULT 1.0,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reinforced TIMESTAMP,
    valid_at TIMESTAMP,                  -- Bi-temporal: when edge became true
    invalid_at TIMESTAMP,                -- Bi-temporal: when edge stopped being true
    FOREIGN KEY (source_node_id) REFERENCES memory_nodes(id),
    FOREIGN KEY (target_node_id) REFERENCES memory_nodes(id)
);

CREATE INDEX idx_memory_edges_source ON memory_edges(source_node_id);
CREATE INDEX idx_memory_edges_target ON memory_edges(target_node_id);
CREATE INDEX idx_memory_edges_rel ON memory_edges(relationship);
CREATE INDEX idx_memory_edges_valid ON memory_edges(valid_at, invalid_at);
```

### Key Design Decisions

1. **Polymorphic reference via (memory_type, memory_id)** — Instead of multiple FK columns or a content-type system, use a simple string type + integer ID pair. This allows graph nodes to reference any memory type without schema changes.
2. **Bi-temporal edges** — `valid_at`/`invalid_at` on edges (not nodes) per Architecture Principle 4.3 (Graphiti-pattern contradiction detection). When a contradiction is found, the old edge gets `invalid_at` and a new edge with the corrected relationship is created.
3. **Confidence as float 0.0-1.0** — Shared vocabulary across nodes and edges. Decay, reinforcement, and consolidation all operate on this scale.
4. **Embedding column on nodes** — Allows vector similarity search within the graph itself, enabling hybrid graph+vector queries without going through the separate vector store.
5. **Metadata JSON column** — Extensible without migrations. Stores LLM extraction results, consolidation provenance, and domain-specific attributes.

### Service Architecture

All services follow the constructor injection pattern (Architecture Principle 1.4):

```python
class SomeService:
    def __init__(self, db: Session):
        self.db = db
    # ...
```

Background tasks use the event bus + arq pattern (Architecture Principle 4.7):

```python
# Dispatched via event bus
await event_bus.emit("memory.consolidate", {"user_id": user_id})

# Handled by persistent job
async def handle_consolidate(ctx, user_id: int):
    service = MemoryConsolidationService(ctx["db"])
    return await service.consolidate(user_id)
```

---

## Definition of Done

- [ ] All 6 memory evolution capabilities implemented
- [ ] Memory graph services in `services/memory/`
- [ ] Graph models with proper indexes and constraints
- [ ] Alembic migration applies and rolls back cleanly
- [ ] Graph construction from existing memories works
- [ ] Consolidation merges similar episodic memories into semantic
- [ ] Evolution applies decay and reinforcement
- [ ] Cross-domain connections link different memory types
- [ ] Temporal queries and pattern detection work
- [ ] API endpoints with ownership checks and response_model
- [ ] Frontend API client typed with TypeScript
- [ ] All tests passing (existing + new ≥ 80% coverage)
- [ ] `make lint` + `make format` clean
- [ ] `make hooks-merge` passes

---

## Readiness for Next Version

v1.07 is complete when the memory graph is a living, self-organizing structure. The following versions can then proceed:

- **v1.14 (Advanced Intelligence)** can build graph-powered reasoning on top of the knowledge graph
- **v1.10 (Planning & Orchestration)** can use graph traversal for dependency analysis
- **v1.11 (Interaction)** can leverage cross-domain connections for context-aware suggestions
- **v1.08 (Awareness Expansion)** awareness data feeds into graph nodes via cross-domain links
