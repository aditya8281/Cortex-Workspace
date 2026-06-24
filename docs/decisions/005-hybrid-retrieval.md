# ADR-005: Hybrid Retrieval Architecture

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code

## Context

Cortex needs to retrieve relevant memory items, documents, and knowledge graph nodes. No single retrieval method covers all use cases: vector search misses keyword matches, full-text misses semantic similarity, graph misses content.

## Decision

Three-source retrieval merged via Reciprocal Rank Fusion (RRF) with Maximal Marginal Relevance (MMR) diversity reranking:
- **Vector search** — Semantic similarity via embeddings
- **Full-text search** — Keyword matching via PostgreSQL
- **Graph traversal** — Relationship-based retrieval via knowledge graph

## Consequences

### Positive
- Best-in-class retrieval: covers semantic, keyword, and relationship queries
- RRF provides robust fusion without weight tuning
- MMR prevents redundant results

### Negative
- More complex than single-source retrieval
- Higher latency (three queries + fusion)
- Requires all three sources to be populated

## Alternatives Considered

1. **Vector-only** — Rejected. Too narrow, misses keyword matches.
2. **Full-text-only** — Rejected. No semantic understanding.
3. **Graph-only** — Rejected. No content retrieval.

## Related

- `backend/app/services/hybrid_retrieval.py` — Implementation (307 lines)
