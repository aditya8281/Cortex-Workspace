# ADR-013: Code-Aware Knowledge Graph

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code

## Context

Cortex needs to understand code structure — imports, calls, inheritance — to provide intelligent retrieval and context. A knowledge graph captures these relationships.

## Decision

Extract code edges (import, call, inheritance) from source files. Store in PostgreSQL JSONB. Graph-enhanced retrieval via RRF.

## Consequences

### Positive
- Unique capability no other repo has
- Enables code-aware retrieval (find all callers of a function)
- Foundation for future graph intelligence features

### Negative
- Regex-only extraction is brittle (current)
- LLM extraction is expensive (future enhancement)

## Related

- `backend/app/services/graph_builder.py` — Implementation (412 lines)
- `backend/app/services/entity_extractor.py` — Implementation (220 lines)
