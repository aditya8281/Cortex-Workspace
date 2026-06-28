Last updated: 2026-06-28

# ADR-002: PostgreSQL as Primary Database

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code

## Context

Cortex needs a primary database for all platform data: user accounts, memory items, vaults, knowledge graph edges, background tasks, and configuration. The system requires JSONB support, FK constraints, GIN indexes, and concurrent access for multi-agent scenarios.

Reference repos use: PostgreSQL 16 (reference architecture, Open WebUI), SQLite (Mem0, AnythingLLM — single-user, scale-limited), Prisma (AnythingLLM — less control).

## Decision

Use PostgreSQL 16 as the primary database for all platform data.

## Consequences

### Positive
- Proven at scale with concurrent access (multi-agent scenarios)
- JSONB for flexible data without schema migrations
- GIN indexes for efficient JSON queries
- FK constraints for data integrity
- 25+ migrations already in place

### Negative
- Requires running PostgreSQL instance (Docker or native)
- Desktop mode needs embedded alternative or bundled PostgreSQL

## Alternatives Considered

1. **SQLite** — Rejected. Scale limitations, single-writer, no concurrent access.
2. **Prisma** — Rejected. Less control, adds abstraction layer.
3. **Neo4j** — Rejected. Separate process, Java runtime, overkill for primary storage.

## Related

- `docker-compose.yml` — PostgreSQL service definition
- `backend/app/core/database.py` — Connection management
- `migrations/` — Schema migrations
