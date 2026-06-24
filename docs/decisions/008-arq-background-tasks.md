# ADR-008: Arq for Background Tasks

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code
**See also:** ADR-016 (Event-Driven Runner — proposed revision)

## Context

Cortex needs background task processing for long-running operations: memory consolidation, embedding generation, health checks, scheduled automations.

## Current Decision

Use arq (Redis-based) for background task queue. Cron health check every 30 minutes.

## Proposed Revision (ADR-016)

Add event-driven runner with persistence, PID tracking, restart-safety. Keep arq for heavy jobs, add event bus for lightweight triggers.

## Consequences

### Positive
- Lightweight, async-native, Redis-backed
- Proper task persistence and retry

### Negative
- asyncio tasks in current implementation lost on restart
- No event triggers for reactive workflows

## Alternatives Considered

1. **Celery** — Rejected. Too heavy.
2. **Custom scheduler** — Rejected. Adds complexity.

## Related

- `backend/app/tasks/worker.py` — Task registration
