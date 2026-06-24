# ADR-010: TDD with SQLite In-Memory Tests

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code

## Context

Cortex needs a testing strategy that's fast, isolated, and doesn't require external services.

## Decision

Use SQLite in-memory engine for tests with:
- JSONB → JSON compiler for compatibility
- Transaction rollback isolation
- 13 blanket-mocked external services

## Consequences

### Positive
- Fast test execution
- No external dependencies
- Complete isolation between tests

### Negative
- SQLite behaves differently from PostgreSQL (JSONB, etc.)
- Mocked services may miss integration issues

## Related

- `tests/conftest.py` — Test configuration
