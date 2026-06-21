# Phase 1: Foundation Stability & Bug Fixes

## Context

The codebase has gone through rapid iteration. Many foundational bugs have been fixed (route shadowing, ownership checks, DB enum mismatches, duplicate code), but more work is needed to reach a stable baseline.

## Goals

- Achieve zero critical bugs
- All endpoints have proper auth and ownership checks
- All frontend pages consume real API data (no placeholders)
- Database schema is consistent with models
- Test coverage reaches 80%+ for backend, 60%+ for frontend

## Key Deliverables

| # | Deliverable | Description | Status |
|---|-------------|-------------|--------|
| 1 | Route ordering fix | All static routes before parameterized | ✅ DONE |
| 2 | Ownership checks | IDOR prevention on all user-scoped endpoints | ✅ DONE |
| 3 | DB enum sync | DocumentType enum matches model | ✅ DONE |
| 4 | LongTermMemory migration | Table creation + env.py imports | ✅ DONE |
| 5 | Duplicate code removal | Consolidate API clients, remove dead code | 🟡 PARTIAL |
| 6 | Backend test coverage | Add tests for all untested routers | 🔴 TODO |
| 7 | Frontend test coverage | Add tests for all pages | 🔴 TODO |
| 8 | API contract validation | Verify frontend types match backend schemas | 🔴 TODO |
| 9 | Error handling audit | Replace silent catches with proper logging | 🔴 TODO |
| 10 | Configuration audit | Verify all env vars documented and used | 🔴 TODO |

## Validation Checkpoints

- [ ] `make lint` passes with zero warnings
- [ ] `make test` passes with 80%+ coverage
- [ ] `npx tsc --noEmit` passes
- [ ] `npx next build` succeeds
- [ ] Manual smoke test of all pages

## Dependencies

None (this is the foundation)

## Complexity

M (medium — mostly systematic fixes)
