# Architecture Findings

## Mem0 — Pipeline Architecture

**Core insight:** Memory is a pipeline, not a database. LLM extracts facts → facts are embedded → facts are stored → facts are searched with triple-signal scoring.

```
┌─────────────────────────────────────────────────┐
│              Memory (Orchestrator)               │
│  mem0/memory/main.py                            │
│                                                  │
│  ┌────────┐ ┌──────────┐ ┌────────────┐ ┌─────┐│
│  │  LLM   │ │ Embedder │ │ VectorStore│ │Rerank││
│  │(extract│ │(vectors) │ │(primary DB)│ │     ││
│  │ & reason)│ │          │ │            │ │     ││
│  └────────┘ └──────────┘ └────────────┘ └─────┘│
│                                                  │
│  ┌──────────────┐ ┌────────────┐ ┌────────────┐│
│  │SQLiteManager │ │Entity Store│ │ Telemetry  ││
│  │(history audit)│ │(vector DB) │ │ (PostHog)  ││
│  └──────────────┘ └────────────┘ └────────────┘│
└─────────────────────────────────────────────────┘
```

**Key abstraction boundaries:**
- `LLMBase` — 18 providers (OpenAI, Anthropic, Gemini, Ollama, etc.)
- `EmbeddingBase` — 8 providers (OpenAI, Azure, Ollama, HuggingFace, etc.)
- `VectorStoreBase` — 24 backends (Qdrant, Chroma, PGVector, FAISS, Redis, etc.)
- `BaseReranker` — 5 implementations (Cohere, SentenceTransformer, etc.)

**Service boundary pattern:** Factory + config dict. Each subsystem is swappable via `MemoryConfig(provider="x", config={...})`.

**What's interesting:**
- Memory ≠ conversation. LLM extracts distilled facts, not raw messages.
- Entity store is a second vector collection, not a graph DB.
- SQLite for audit trail (history of every memory mutation).
- Triple-signal retrieval: semantic + BM25 + entity boost.

---

## Graphiti — Temporal Knowledge Graph Architecture

**Core insight:** Every fact is bi-temporal (real-world time + system time). Facts are never deleted — they're invalidated. The LLM deduplicates and resolves contradictions.

```
┌─────────────────────────────────────────────────────────┐
│                    Graphiti (Main Class)                  │
│  graphiti.py — orchestrator                              │
├──────────┬──────────┬───────────┬──────────┬────────────┤
│  NODES   │  EDGES   │  SEARCH   │ PROMPTS  │   DRIVER   │
│          │          │           │          │            │
│ EntityN  │ EntityE  │ BM25      │ extract  │ GraphDriver│
│ EpisodeN │ EpisodeE │ cosine    │ dedupe   │ ├─ Neo4j   │
│ Community│ Community│ BFS       │ summarize│ ├─ FalkorDB │
│ SagaN    │ HasEpiE  │           │          │ ├─ Kuzu    │
│          │ NextEpiE │ Rerankers │          │ └─ Neptune │
│          │          │ RRF/MMR/CrossEnc│    │            │
└──────────┴──────────┴───────────┴──────────┴────────────┘
```

**4 node types:** EntityNode, EpisodeNode, CommunityNode, SagaNode
**5 edge types:** EntityEdge (RELATES_TO), EpisodicEdge (MENTIONS), CommunityEdge (HAS_MEMBER), HasEpisodeEdge, NextEpisodeEdge

**Key abstraction boundaries:**
- `GraphDriver` (ABC) — composite operations layer, each node/edge type has its own operations interface
- `LLMClient` (ABC) — OpenAI by default
- `EmbedderClient` (ABC) — OpenAI by default
- `CrossEncoderClient` (ABC) — multiple reranker backends

**Service boundary pattern:** Composite driver with per-type operations. Each node/edge type has its own operations class. Adding a new DB means implementing ~11 interfaces × node/edge types.

**What's interesting:**
- Bi-temporal facts: `valid_at`/`invalid_at` (real world) + `created_at`/`expired_at` (system).
- LLM-assisted entity deduplication (not string matching).
- Automatic contradiction detection + invalidation.
- Community detection via label propagation + LLM summaries.
- Saga pattern for episode sequences (conversations as linked episode chains).
- Semantic fact embeddings (not just entity name embeddings).

---

## Cortex Current — Monolithic Service Architecture

**Core insight:** Backend is a FastAPI app with SQLAlchemy models and Qdrant for vectors. Memory and graph are separate subsystems with no consolidation mechanism.

```
┌─────────────────────────────────────────────────────────┐
│                 FastAPI (backend/app/)                    │
├──────────┬──────────┬───────────┬──────────┬────────────┤
│ MEMORY   │  GRAPH   │  VECTOR   │   RAG    │  INDEXING  │
│          │          │           │          │            │
│ LTM model│ GraphNode│ Qdrant    │ Hybrid   │ Incremental│
│ LTM svc  │ GraphEdge│ (768-dim) │ Retrieval│ Indexer    │
│ Knowledge│ GraphBldr│           │ RAG Pipe │ Chunker    │
│ Manager  │ CrossFile│ Embedding │          │ DocIndexer │
│          │ Search   │ 3-tier    │          │            │
└──────────┴──────────┴───────────┴──────────┴────────────┘
```

**Current implementations:**
- **Memory:** `LongTermMemory` model (5 categories, confidence, decay), `LongTermMemoryService`, `MemoryManager` (knowledge entries)
- **Graph:** `GraphNode`/`GraphEdge` in PostgreSQL (4 edge types: calls, imports, inherits, contains)
- **Vector:** Qdrant (768-dim cosine), `cortex_code` + `cortex_memory` collections
- **Embedding:** 3-tier fallback (ONNX → Ollama → mock)
- **RAG:** `HybridRetrievalV2` (vector + fulltext + graph), `RAGPipeline` (token-budgeted context)
- **Indexing:** Incremental (hash-based), semantic chunking, 17 document parsers

**What's missing vs. reference repos:**
- No LLM-based entity extraction (regex only in graph builder)
- No temporal knowledge (first_seen/last_seen only)
- No memory consolidation/deduplication
- No community detection
- No MMR diversity reranking
- No bi-temporal facts
- No contradiction detection
- Graph is code-structure only (not semantic/conversational)

---

## Comparative Architecture Summary

| Dimension | Mem0 | Graphiti | Cortex |
|-----------|------|----------|--------|
| **Core paradigm** | Pipeline (extract → embed → store → search) | Temporal KG (episode → entity → community) | Service layer (model → service → API) |
| **Primary storage** | Vector store + SQLite | Graph DB (Neo4j) | PostgreSQL + Qdrant |
| **Memory representation** | Distilled facts (15-80 words) | Bi-temporal entity edges | Typed memories (5 categories) |
| **Entity model** | Vector-stored entities with linked_memory_ids | Graph nodes with relationships | Graph nodes linked to code chunks |
| **Temporal model** | None (created_at/updated_at only) | Bi-temporal (valid/invalid + created/expired) | first_seen/last_seen only |
| **Deduplication** | LLM-based (V3 additive extraction) | LLM-based (dedupe_nodes, dedupe_edges) | None |
| **Contradiction handling** | LLM decides ADD/UPDATE/DELETE | Automatic invalidation with temporal preservation | None |
| **Search** | Triple-signal (semantic + BM25 + entity boost) | Multi-layer (4 node types × search methods × rerankers) | Hybrid (vector + fulltext + graph) |
| **Reranking** | Optional (Cohere, SentenceTransformer, etc.) | Configurable (RRF, MMR, CrossEncoder, NodeDistance) | None (score normalization only) |
| **Service abstraction** | ABC + factory (provider → class path) | ABC + composite driver operations | Concrete classes, constructor injection |
| **Multi-tenancy** | user_id / agent_id / run_id scoping | group_id partitioning | user_id scoping |
| **Background jobs** | None (synchronous pipeline) | None (synchronous pipeline) | arq task queue |
