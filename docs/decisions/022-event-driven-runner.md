Last updated: 2026-06-28

# ADR-022: Event-Driven Runner (Replaces ADR-008)

**Status:** Proposed
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code
**Supersedes:** ADR-008 (Arq for Background Tasks — partial)
**Phase:** V3 Phase 3

## Context

ADR-008 used arq for background tasks, but asyncio tasks are lost on restart and there are no event triggers for reactive workflows. The daemon mode requires persistent, restart-safe task execution.

## Decision

Add event-driven runner with persistence, PID tracking, restart-safety. Keep arq for heavy jobs, add event bus for lightweight triggers.

## Consequences

### Positive
- Persistent tasks survive restarts
- Event-driven workflows (reactive)
- PID tracking for daemon mode

### Negative
- Two systems to maintain (arq + event bus)
- More complex than single system

## Related

- `backend/app/tasks/worker.py` — Current implementation
