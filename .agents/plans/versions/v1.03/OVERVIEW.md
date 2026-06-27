# v1.03: Memory Foundation — CORTEX

**Document:** Version 1.03 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Capability Delivery

---

## Objective

Build the foundational memory system: episodic memory, semantic memory, working memory, memory graph, forgetting mechanism, memory search, and temporal memory. This is the first capability-delivering version — the point where Cortex transitions from structural scaffolding to genuine intelligence.

---

## Question

"Can Cortex remember?"

---

## What This Version Delivers

After completing v1.03, Cortex has:

- **Episodic memory** — Stores experiences, events, and conversations with full temporal context. Each memory carries emotion tags, importance scores, and confidence levels that decay over time.
- **Semantic memory** — Stores facts, preferences, concepts, and knowledge. Categorized with source tracking and confidence scoring for knowledge reliability.
- **Working memory** — Session-scoped context with active/buffer/archive slots. Auto-expires. Enables multi-turn conversations and task continuity.
- **Memory graph** — Nodes and edges connecting related memories. Supports traversal, edge strengthening/weakening, and automatic connection discovery.
- **Forgetting mechanism** — Intelligent Ebbinghaus-style decay. Memories fade based on recency, access frequency, and importance. Low-confidence memories are garbage-collected.
- **Memory search** — Cross-type search with temporal scoring, importance weighting, and access frequency boosting.
- **Temporal memory** — Time-aware relevance scoring. Memories created or accessed at similar times of day, day of week, or season score higher for contextual retrieval.

---

## reference architecture Feature Traceability

This version addresses the following reference architecture-derived features:

| reference architecture Feature | Cortex Implementation | Notes |
|------------------|----------------------|-------|
| Context persistence across sessions | Working Memory + Episodic Memory | reference architecture had session persistence via SQLite; we generalize to typed memory |
| Knowledge accumulation | Semantic Memory | reference architecture accumulated user preferences manually; we build a categorized knowledge store |
| Conversation memory | Episodic Memory | reference architecture stored conversation history; we add temporal context and emotion tagging |
| User preference learning | Semantic Memory (category="preference") | reference architecture had hardcoded preference tracking; we make it generic |
| Importance-based retrieval | Temporal Scoring + Memory Search | reference architecture had no retrieval ranking; we add multi-signal scoring |
| Memory consolidation | Forgetting Service (future: P07 in v1.07) | reference architecture had no consolidation; this version lays the foundation |
| Graph-based connections | Memory Graph | reference architecture had no graph; this is a new capability not present in reference architecture |

---

## Capability Mapping (120-Capability Model)

This version implements 7 of the 120 total capabilities, all in the **Memory** domain:

| ID | Name | Domain | Priority | Capabilities Remaining After This |
|----|------|--------|----------|----------------------------------|
| M1 | Episodic Memory | Memory | Foundation | 113 |
| M2 | Semantic Memory | Memory | Foundation | 112 |
| M4 | Working Memory | Memory | Foundation | 111 |
| M6 | Memory Graph | Memory | Foundation | 110 |
| M7 | Forgetting | Memory | Core | 109 |
| M10 | Memory Search | Memory | Foundation | 108 |
| M12 | Temporal Memory | Memory | Core | 107 |

**Total: 7 capabilities (cumulative: 7/120)**

### Downstream Capability Dependencies

These future capabilities directly depend on v1.03 capabilities:

| Future Capability | Depends On (v1.03) | Delivered In |
|-------------------|---------------------|--------------|
| M3: Long-Term Memory | M1, M2 | v1.07 |
| M5: Memory Consolidation | M1, M2, M7 | v1.07 |
| M8: Emotional Memory | M1, M12 | v1.07 |
| M9: Contextual Memory | M4, M6 | v1.07 |
| M11: Memory Decay | M7, M12 | v1.07 |
| M13: Memory Transfer | M1, M2, M6 | v1.07 |
| C1: Attention | M4, M10 | v1.06 |
| C2: Reasoning | M2, M6 | v1.06 |
| C3: Decision Making | M2, M6, M10 | v1.06 |
| P1: Goal Management | M2, M4 | v1.10 |
| P2: Task Planning | M2, M4, M6 | v1.10 |

---

## Phases

| Phase | Name | Focus | Complexity | Capabilities Delivered |
|-------|------|-------|------------|----------------------|
| P01 | Memory Models & Schema | Database models, Pydantic schemas, migrations | Medium | Foundation for all |
| P02 | Episodic & Semantic Memory | Core memory services, CRUD, deduplication | High | M1, M2 |
| P03 | Working Memory & Graph | Session context, memory connections, traversal | High | M4, M6 |
| P04 | Search & Forgetting | Retrieval, intelligent fading, temporal scoring | Medium | M7, M10, M12 |
| P05 | API & Integration | REST endpoints, frontend hooks, OpenAPI, E2E | Medium | Integration |

---

## Dependencies

**Depends on:**
- v1.02 (Backend Architecture — event system, domain services, middleware pipeline, auth system)
- v1.01 (Repository Structure — file placement conventions, `models/memory/` package structure)

**Blocks:**
- v1.07 (Memory Evolution — consolidation, long-term, emotional, contextual memory)
- v1.06 (Cognition & Execution Core — reasoning and decision-making need memory access)
- v1.09 (Learning Foundation — learning requires memory to store learned patterns)
- v1.10 (Planning & Orchestration — planning needs semantic memory for knowledge and working memory for context)

---

## Architecture Principle Cross-References

| Principle | How v1.03 Satisfies It |
|-----------|----------------------|
| **AD-001: Domain-Driven Architecture** | Memory is a distinct bounded context with its own models, services, and API surface. Clean separation from other domains. |
| **AD-002: Event-Driven Communication** | Memory services emit events on creation, update, and forgetting. Downstream consumers (e.g., graph auto-connection) react to these events. |
| **AD-003: Privacy as Architecture** | All memory queries are scoped by `user_id`. Cross-user memory access is impossible at the query level. Forgetting permanently deletes data. |
| **AD-004: Memory-First Intelligence** | This version IS the memory-first principle. Every future intelligence capability builds on these memory foundations. |
| **AD-005: Layered Maturity Model** | v1.03 implements Foundation-tier memory. Higher tiers (consolidation, emotional, transfer) come in v1.07. |
| **AD-008: Gradual Capability Expansion** | 7 capabilities in 5 phases. Each phase is independently testable and deployable. |
| **AD-011: Simplicity Over Completeness** | Search starts with ILIKE fulltext. Vector search and graph traversal are simplified. Advanced algorithms deferred to v1.07. |
| **AD-012: Architectural Evolution** | Schema design allows adding columns without migration pain. Service interfaces are extensible. |

---

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation | Phase |
|------|-----------|--------|------------|-------|
| Migration conflicts with v1.02 models | Medium | High | Use separate `memory/` model package. Test migration up/down. | P01 |
| Qdrant not available for vector search | High | Medium | Implement fulltext search first. Vector search is enhancement, not requirement. | P04 |
| Memory graph performance degrades at scale | Medium | High | Index on `(source_id, target_id)`. Limit traversal depth. Defer graph DB to v1.07. | P03 |
| Forgetting deletes important memories | Low | Critical | Minimum confidence threshold of 0.1. Exponential decay floor at 0.05. User override capability. | P04 |
| Working memory session leaks across users | Low | Critical | `session_id` + `user_id` composite filter on all queries. | P03 |
| Auto-connection creates noisy graph | Medium | Medium | Confidence threshold for auto-edges. Limit edges per node. Manual pruning API. | P03 |
| Search returns irrelevant results | Medium | Medium | Multi-signal scoring (recency + importance + frequency). Configurable weights. | P04 |
| API rate limiting blocks legitimate memory operations | Low | Medium | Memory endpoints use standard rate limits. Bulk operations use batch API. | P05 |
| Pydantic v2 migration breaks schema validation | Low | High | Use `from_attributes = True` consistently. Test all schema conversions. | P01 |
| SQLite test vs PostgreSQL production divergence | Medium | Medium | Test with `JSONB → JSON` compilation in conftest. Integration tests on PostgreSQL. | All |

---

## Downstream Dependency Impact

If v1.03 fails or is significantly delayed:

| Affected Version | Impact | Recovery |
|------------------|--------|----------|
| **v1.07 (Memory Evolution)** | Cannot start. Consolidation, long-term, emotional memory all depend on foundation models. | Must complete v1.03 first. No workaround. |
| **v1.06 (Cognition & Execution)** | Reasoning and decision-making lack memory context. Agent loop cannot make informed decisions. | Partial: can stub memory with in-memory dict, but loses persistence. |
| **v1.09 (Learning Foundation)** | Cannot store learned patterns or user behavior models. | Must complete v1.03 first. |
| **v1.10 (Planning & Orchestration)** | Planning cannot access knowledge base or maintain session context. | Partial: can use hardcoded plans, loses adaptive planning. |
| **v1.11 (Interaction & Communication)** | Chat memory is lost between sessions. Conversation context is ephemeral. | Degrades to stateless chat. Loses major differentiator. |

---

## Estimated Duration

5-7 days (2 developers) or 8-11 days (1 developer).

---

## Security Considerations

- **Data isolation:** Every memory query includes `user_id` filter. No cross-user data leakage possible.
- **Forgetting compliance:** GDPR Article 17 — forgetting service provides permanent deletion, not soft-delete.
- **Input validation:** Pydantic schemas enforce content length limits (max 10,000 chars for memory content).
- **Rate limiting:** Memory creation endpoints are rate-limited to prevent abuse (100 creates/hour/user).
- **No secrets in memory:** Content validation rejects patterns matching API keys, passwords, tokens.
- **Migration safety:** All migrations have rollback commands documented. `alembic downgrade -1` tested.

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Memory create latency | < 50ms | p95 from API call to response |
| Memory search latency | < 200ms | p95 for queries up to 10,000 memories |
| Graph traversal (depth 3) | < 100ms | p95 for 3-hop traversal |
| Forgetting batch (1000 memories) | < 5s | Batch decay computation |
| Working memory query | < 20ms | p95 for session-scoped active items |
| API endpoint response time | < 100ms | p95 excluding search |

---

## Integration Tests

This version requires the following integration test suites:

1. **Memory CRUD Lifecycle** — Create → Retrieve → Update → Forget → Verify deleted
2. **Cross-Type Search** — Create episodic + semantic, search returns both types
3. **Graph Connectivity** — Create nodes → Add edges → Traverse → Verify connections
4. **Temporal Scoring** — Create memories at different times → Score → Verify ranking
5. **Forgetting Pipeline** — Create memories → Apply decay → Verify confidence reduction → Verify garbage collection
6. **API Authentication** — Unauthenticated requests → 401. Wrong user → 403.
7. **Migration Roundtrip** — `make migrate` → `alembic downgrade -1` → `make migrate` → No errors

---

## Definition of Done

- [ ] All 7 memory capabilities implemented and tested
- [ ] Memory services in `backend/app/services/memory/` (5 modules: episodic, semantic, working, graph, search/decay/temporal)
- [ ] Memory models in `backend/app/models/memory/` (4 model files + __init__)
- [ ] Memory schemas in `backend/app/schemas/memory/` (4 schema files + __init__)
- [ ] Memory API endpoints in `backend/app/api/v1/memory/` (4 route files + __init__)
- [ ] Frontend API client in `frontend/features/memory/api.ts`
- [ ] Frontend hooks in `frontend/features/memory/hooks/`
- [ ] Unit tests: 90%+ coverage on memory services
- [ ] Integration tests: all 7 test suites passing
- [ ] Migration applies cleanly and rolls back cleanly
- [ ] `make test` passes (0 failures)
- [ ] `make lint` passes (0 errors)
- [ ] OpenAPI schema shows all memory endpoints at `/docs`
- [ ] Performance targets met (benchmarked)
- [ ] Security review: no cross-user data leakage, no secret injection

---

## Readiness for Next Version

v1.03 is the **critical path bottleneck** for the entire memory domain. Once complete:
- v1.07 (Memory Evolution) can begin consolidation and advanced memory features
- v1.06 (Cognition) can use memory for reasoning and decision-making
- v1.04 (Awareness Foundation) can begin in parallel — it has no dependency on memory
