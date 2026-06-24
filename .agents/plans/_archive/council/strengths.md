# CORTEX Strengths — Evidence-Based

**Date:** 2026-06-25
**Purpose:** What Cortex does well, verified against reference repositories.

---

## 1. Infrastructure — Superior to All References

### Database (PostgreSQL 16)
- 33 tables with proper FK constraints, soft deletes, JSONB for flexible data
- 6 active migrations in clean chain, 26 archived showing history
- Schema debt documented inline (c00000000005)
- **Better than:** Odysseus (SQLite, 7 tables), Mem0 (SQLite for history), AnythingLLM (SQLite+Prisma)
- **Evidence:** migration c00000000003 adds missing FK indexes and unique constraints — shows active schema maintenance

### Authentication
- Two-password model (login + vault, separate encryption contexts)
- JWT access (30min) + refresh (7-day rotation) in httpOnly cookies
- CSRF double-submit pattern
- Rate limiting with sliding window (5 failures → 15min block)
- Auth event audit trail
- **Better than:** Odysseus (single password, Bearer tokens), Mem0 (no auth), AnythingLLM (basic)
- **Evidence:** Full auth flow tested — register → login → token → protected endpoint (test_refresh.py, 11 tests)

### Frontend (Next.js 15 + React 19)
- 14 real page routes, 18 UI components, 11 API client modules
- "Warm Neural Dark" design system with tokens
- 60+ TypeScript interfaces mapping to backend schemas
- Vault module is a full file manager (6 custom hooks)
- Models module has 30+ API methods
- Agent module has real SSE streaming
- **Better than:** Odysseus (vanilla JS SPA), Mem0 (no frontend), AnythingLLM (basic React)
- **Evidence:** ~21,800 lines of real, production code. No stubs in frontend components.

### Security Depth
- CSRF, rate limiting, SSRF protection (`_is_private_url`), path traversal prevention
- HMAC approval tokens for dangerous agent tools
- Blocked command patterns (rm -rf /, etc.)
- Workspace sandboxing for agent tools
- **Better than:** Odysseus (basic), Mem0 (none), Continue (basic)
- **Evidence:** tools.py lines 100-160 implement comprehensive security checks

---

## 2. Memory System — Unique Capabilities

### Confidence-Based Memory Scoring
- LongTermMemory has confidence scores with automatic decay (0.95x per 30 days)
- Access-count tracking for reinforcement
- **Unique:** Neither Mem0 nor Graphiti have explicit confidence scoring
- **Evidence:** long_term_memory.py (113 lines) — `decay_confidence()` and `reinforce()` methods

### Time-Based Memory Decay
- Memories decay over time unless reinforced by access
- **Unique:** No reference repository implements this
- **Evidence:** `confidence * (0.95 ** (days_since_access / 30))` formula

### Embedding Cache with TTL
- EmbeddingCache table prevents redundant embedding computations
- **Better than:** Mem0 (no caching), Graphiti (no caching), Odysseus (no caching)
- **Evidence:** embedding_cache.py (150 lines) with TTL-based invalidation

---

## 3. RAG Pipeline — Best-in-Class Retrieval

### Hybrid Retrieval (HybridRetrievalV2)
- Three sources in parallel: vector + fulltext + graph
- RRF (Reciprocal Rank Fusion) for score merging
- MMR (Maximal Marginal Relevance) for diversity reranking
- Token-budgeted context injection
- **Better than:** Odysseus (ChromaDB only), Mem0 (triple-signal but no graph), AnythingLLM (single vector)
- **Evidence:** hybrid_retrieval.py (307 lines), fulltext_search.py (286 lines)

### Full-Text Search
- PostgreSQL tsvector/tsquery with stemming
- BM25-style weights
- Snippet highlighting
- **Better than:** Odysseus (none), Mem0 (BM25 but no stemming)
- **Evidence:** fulltext_search.py implements `websearch_to_tsquery` with language config

### Retrieval Metrics
- Explicit retrieval quality tracking
- **Better than:** All reference repos — none have retrieval metrics
- **Evidence:** retrieval_metrics.py (90 lines)

---

## 4. Knowledge Graph — Unique Code Intelligence

### Code-Aware Graph Building
- Extracts import, call, inheritance edges from code
- Graph nodes for functions, classes, modules
- Graph edges with relationship types
- **Unique:** No reference repository builds knowledge graphs from code
- **Evidence:** graph_builder.py (412 lines), entity_extractor.py (220 lines)

### Graph-Enhanced Retrieval
- Graph results merged into hybrid retrieval via RRF
- Graph traversal for related entities
- **Unique:** Mem0 has entity store but no graph traversal. Graphiti has temporal KG but no code intelligence.

---

## 5. Indexing Pipeline — Unique Capabilities

### Incremental Indexing
- Skip unchanged files (mtime-based)
- Batch + real-time tracks
- **Unique:** No reference repository has incremental code indexing
- **Evidence:** incremental_indexer.py (345 lines)

### 17 Document Parsers
- PDF, Markdown, DOCX, HTML, EPUB, PPTX, XLSX, notebook, media, archive, font, iCal, vCard, OpenDocument, GIS
- **Better than:** sist2 (15 parsers), Odysseus (basic), Mem0 (text only)
- **Evidence:** services/parsers/ directory with 10+ parser files

### Code-Aware Chunking
- Chunks by function, class, module boundaries
- Not generic text splitting
- **Better than:** LlamaIndex (generic), Odysseus (none), Mem0 (none)
- **Evidence:** chunker.py (235 lines) — function/class/module boundary detection

### Semantic Chunking
- Document-type-aware strategies
- **Comparable to:** LlamaIndex HierarchicalNodeParser
- **Evidence:** semantic_chunker.py (206 lines)

---

## 6. Model Management — Comprehensive

### Three-Source Catalog
- OCI Registry + Cloud API + Local API (Ollama)
- **Better than:** Odysseus (basic list), ollama-catalog (single source)
- **Evidence:** ollama_catalog.py (693 lines)

### Hardware-Aware Recommendations
- GPU, RAM, disk detection
- Workload-based scoring
- **Better than:** All reference repos — none do hardware-aware recommendations
- **Evidence:** recommendation.py (525 lines), hardware.py (359 lines)

### Background Download Manager
- Progress tracking, retry, pause/resume
- **Better than:** Odysseus (basic), ollama-catalog (basic)
- **Evidence:** model_downloader.py (520 lines)

---

## 7. Vault — Unique Encryption Model

### Fernet Encryption with Secure Password Cache
- Per-user vault with separate password
- Per-file salt derivation
- SecurePasswordCache wipes password from memory on pop
- **Better than:** Odysseus (basic Fernet), Mem0 (none), AnythingLLM (none)
- **Evidence:** vault_service.py (806 lines) — largest service in codebase

---

## 8. Governance — Unmatched

### Multi-Agent Development Ecosystem
- 12 mandatory workflow rules
- 11 automated hooks across 4 phases
- 10 workflow definitions
- Permission model (Read-only → Contributor → Reviewer → Architect)
- Clarification rules (MUST ask vs MAY proceed)
- Reflection framework (mandatory before completion)
- 7 strategic commands (/project:reflect, review, challenge, health, architecture, ideas, improve)
- **Unique:** No reference repository has anything comparable
- **Evidence:** GOVERNANCE.md (319 lines), WORKFLOWS.md (460 lines), DEVELOPER_GUIDE.md (504 lines)

### Test Coverage
- 341 tests across 42 files
- SQLite in-memory with transaction rollback isolation
- 13 blanket-mocked external services
- Tests run without real PostgreSQL, Redis, or Qdrant
- **Better than:** Odysseus (~150 tests), Mem0 (~100 tests)
- **Evidence:** conftest.py architecture is sophisticated — JSONB→JSON compiler, nested transaction rollback

---

## 9. Docker — Production-Ready

- Multi-stage build (frontend → backend)
- Non-root user (cortex)
- Healthcheck (GET /api/v1/health/live)
- Localhost-only binding (127.0.0.1)
- uv for fast dependency resolution
- **Better than:** Odysseus (basic), Mem0 (none)
- **Evidence:** Dockerfile is well-structured with proper layer caching

---

## 10. Graceful Degradation — Resilient Architecture

- Redis fails open (in-memory fallback for rate limiting, CSRF, caching)
- Qdrant uses circuit breakers
- Ollama uses mock embeddings when unavailable
- LLM falls back to keyword matching when no provider configured
- **Evidence:** redis.py returns None on failure, embedding_service.py has 3-tier fallback

---

## Summary: What Cortex Is Best At

| Rank | Capability | Evidence |
|------|-----------|----------|
| 1 | Infrastructure (DB, auth, Docker) | PostgreSQL 16, two-password auth, production Docker |
| 2 | RAG pipeline (hybrid retrieval) | Vector + fulltext + graph + RRF + MMR + token budget |
| 3 | Governance (multi-agent ecosystem) | 12 rules, 11 hooks, 10 workflows, 7 commands |
| 4 | Memory system (confidence + decay) | Unique confidence scoring, time-based decay |
| 5 | Knowledge graph (code intelligence) | Import/call/inheritance edges, graph-enhanced retrieval |
| 6 | Indexing (incremental + 17 parsers) | Skip unchanged, code-aware chunking, broad format support |
| 7 | Model management (3-source catalog) | OCI + Cloud + Local, hardware-aware recommendations |
| 8 | Vault (Fernet + secure cache) | Per-file salt, memory-wiping password cache |
| 9 | Frontend (real, production code) | 21,800 lines, 14 routes, 18 components, SSE streaming |
| 10 | Test infrastructure (341 tests) | SQLite isolation, 13 mocked services, runs without infra |
