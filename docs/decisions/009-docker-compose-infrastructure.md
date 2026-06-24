# ADR-009: Docker Compose for Infrastructure

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code

## Context

Cortex requires PostgreSQL, Redis, and Qdrant for its infrastructure. These services need to be managed consistently across development and production environments.

## Decision

Use Docker Compose for local infrastructure:
- PostgreSQL 16
- Redis 7
- Qdrant v1.18

All services bound to localhost only.

## Consequences

### Positive
- Production-ready infrastructure
- Consistent across environments
- Volume mounts for data persistence
- Health checks for reliability

### Negative
- Requires Docker installed
- Desktop mode needs embedded alternatives

## Related

- `docker-compose.yml` — Service definitions
- `start.sh` — Development launcher
