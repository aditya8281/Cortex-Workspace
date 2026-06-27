# v1.01: Repository Restructure — CORTEX

**Document:** Version 1.01 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Structural Migration + Scaffolding

---

## Objective

Reorganize the Cortex repository into a domain-driven structure, establish frontend feature module architecture, and create comprehensive testing infrastructure. No capability changes. No new features. Pure structural migration and scaffolding that makes the codebase navigable, testable, and prepared for domain evolution.

---

## Question

"Can we navigate the codebase and verify it works?"

---

## Architecture Traceability

This version implements **reference architecture Principle 1: Structure Before Capability** — every restructuring decision maps to a governance artifact:

| Decision | Artifact | Principle |
|----------|----------|-----------|
| Domain-driven service layout | `migration_map.md` | Ownership clarity |
| Feature-module frontend architecture | `frontend_architecture.md` | Module isolation |
| Import migration strategy | `migration_map.md` | Zero-breakage guarantee |
| Testing infrastructure before features | `testing_architecture.md` | Verifiability first |
| Documentation by topic | `documentation_architecture.md` | Discoverability |
| Planning by version | `planning_architecture.md` | Execution traceability |

**Rule:** Every file move, every new directory, every import change has a traced mapping in the migration artifacts. No ad-hoc restructuring.

---

## What This Version Delivers

After completing v1.01, a contributor can:

- **Navigate** — Find any file by understanding the domain structure
- **Own** — Know which domain owns every file
- **Discover** — Find documentation by topic, planning by version
- **Build** — Frontend feature modules load independently with lazy loading
- **Test** — Comprehensive fixture factories, integration harnesses, and CI pipeline exist
- **Verify** — Meta-tests confirm test infrastructure itself works
- **Scale** — New features follow established scaffolding patterns without architectural decisions

---

## Scope

### In Scope

1. Backend service reorganization (flat → domain directories)
2. Backend model reorganization (flat → domain directories)
3. Import migration (update all import paths)
4. Frontend reorganization (flat → feature modules)
5. Frontend feature module scaffolding (conventions, patterns, shared utilities)
6. Documentation reorganization (flat → subdirectories)
7. Planning reorganization (flat → versioned structure)
8. Testing infrastructure (fixtures, harnesses, CI pipeline)

### Out of Scope

- API endpoint reorganization (v1.02)
- Event system (v1.02)
- New capabilities (v1.03+)
- Frontend redesign (v1.11)
- New features (v1.03+)
- Performance optimization (v1.04)

---

## Phases

| Phase | Name | Focus | Complexity | Duration | Dependencies |
|-------|------|-------|------------|----------|--------------|
| **P01** | Backend Services Reorganization | Move flat services to domain directories | Medium | 3-4h | None |
| **P02** | Backend Models Reorganization | Move flat models to domain directories | Medium | 2-3h | P01 |
| **P03** | Import Migration | Update all import paths across codebase | High | 5-7h | P01, P02 |
| **P04** | Frontend Reorganization | Move components to feature modules | Medium | 2-3h | P01-P03 |
| **P05** | Documentation Reorganization | Organize docs by topic | Low | 1-2h | None |
| **P06** | Planning Reorganization | Organize planning by version | Low | 0.5-1h | None |
| **P07** | Frontend Feature Module Scaffolding | Feature module conventions, templates, shared utilities | Medium | 3-4h | P04 |
| **P08** | Testing Infrastructure | Fixture factories, integration harnesses, CI pipeline | Medium-High | 4-5h | P01-P03 |

---

## Dependency Graph

```
    P01 (Backend Services)
     │
     ├──────────┬──────────┐
     ▼          ▼          │
   P02       P05          │  (P05 is independent, can run parallel)
  (Models)   (Docs)       │
     │          │         │
     ▼          │         │
   P03 ◄───────┘         │  (Import Migration needs P01+P02)
  (Imports)              │
     │                   │
     ├──────┬────────────┘
     ▼      ▼
   P04    P08              (P04: Frontend, P08: Testing infra)
  (Frontend)
     │
     ▼
   P07                     (Feature Module Scaffolding)
  (Module Scaffolding)     
     │
     ▼
   P06                     (Planning is independent, runs anywhere)
  (Planning)
```

**Parallelization opportunities:**
- P05 (Docs) can run in parallel with P01-P04 (no code dependency)
- P06 (Planning) can run in parallel with everything
- P08 (Testing) can start after P03 completes (needs stable backend)
- P07 (Scaffolding) depends on P04 completing

---

## Capability Mapping

This version establishes **infrastructure capabilities** that v1.03+ builds upon:

| Infrastructure | Established In | Consumed By |
|---------------|---------------|-------------|
| Domain service structure | P01 | v1.02 (Backend Architecture) |
| Domain model structure | P02 | v1.02, v1.03 |
| Canonical import paths | P03 | All future versions |
| Feature module pattern | P04, P07 | v1.03+ (all frontend features) |
| Feature module conventions | P07 | v1.03+ (all frontend features) |
| Shared API client pattern | P07 | v1.03+ (all API integration) |
| Fixture factory pattern | P08 | v1.02+ (all new services) |
| Integration test harness | P08 | v1.02+ (all multi-service tests) |
| CI test pipeline | P08 | All future versions |

---

## Migration Mapping

This version uses the migration map from Stage 5:
- `.agents/plans/artifacts/migration_map.md`

Every file move follows the exact mapping in that document. No deviations without governance review.

---

## Estimated Duration

**12-20 days** (was 11-18 days in original estimate).

| Phase | Estimated Duration |
|-------|-------------------|
| P01 | 3-4h |
| P02 | 2-3h |
| P03 | 5-7h |
| P04 | 2-3h |
| P05 | 1-2h |
| P06 | 0.5-1h |
| P07 | 3-4h |
| P08 | 4-5h |
| **Total** | **20-29h** (≈3-5 working days) |

*Note: Duration is measured in implementation hours. With review cycles, reflection gates, and batch processing, calendar duration extends to 12-20 days.*

---

## Definition of Done

### Structural Integrity
- [ ] All backend services in domain directories (zero flat files)
- [ ] All backend models in domain directories (zero flat files)
- [ ] All frontend components in feature modules
- [ ] All documentation in subdirectories by topic
- [ ] All planning organized by version

### Import Hygiene
- [ ] Zero imports reference old flat paths
- [ ] `grep -rn "from app.services import" backend/` returns 0 results
- [ ] `grep -rn "from app.models import" backend/` returns 0 results
- [ ] IDE shows no import errors across entire codebase

### Frontend Architecture
- [ ] Feature module template established with `index.ts`, `types.ts`, `api.ts`, `components/`, `hooks/`
- [ ] Feature module conventions documented and enforced
- [ ] Shared utilities in `shared/` (API client, types, hooks)
- [ ] Feature registration pattern for routing and navigation
- [ ] Lazy loading verified for all feature modules
- [ ] `npm run build` succeeds with zero errors
- [ ] `npm test` passes with zero failures

### Testing Infrastructure
- [ ] Fixture factories exist for all domain models
- [ ] Integration test harness configured (DB + Redis + service mocks)
- [ ] Agent system test harness with mock LLM responses
- [ ] Frontend test setup with Vitest, test-utils, mock API handlers
- [ ] Performance baseline captured (API response times, memory, test duration)
- [ ] CI pipeline runs tests and reports coverage
- [ ] Meta-tests verify test infrastructure works

### Verification Gates
- [ ] `make test` passes
- [ ] `make migrate` works
- [ ] `make lint` clean
- [ ] `make format` clean
- [ ] `npm run build` succeeds
- [ ] `npm test` passes
- [ ] `make hooks-merge` passes
- [ ] No functional changes (pure structural migration)

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Import breaks during migration | High | Run full test suite after each phase; grep verification |
| Merge conflicts | Medium | Complete in single branch; commit after each task |
| Forgotten imports | High | IDE refactoring + grep verification + CI pipeline |
| Alembic migration breaks | High | Verify before/after each model move |
| Frontend build breaks | Medium | Run `npm run build` after each change |
| Test infrastructure over-engineering | Low | Keep fixtures simple; avoid abstract patterns |
| Circular imports after restructuring | Medium | Domain boundaries prevent most; verify with import checks |
| Performance regression from reorganization | Low | Capture baseline in P08; compare after completion |

---

## Cross-References

| Document | Reference |
|----------|-----------|
| Architecture Constitution | `.agents/plans/guide.md` |
| Migration Map | `.agents/plans/artifacts/migration_map.md` |
| Repository Architecture | `.agents/plans/artifacts/repository_architecture.md` |
| Frontend Architecture | `.agents/plans/artifacts/frontend_architecture.md` |
| Backend Architecture | `.agents/plans/artifacts/backend_architecture.md` |
| Documentation Architecture | `.agents/plans/artifacts/documentation_architecture.md` |
| Planning Architecture | `.agents/plans/artifacts/planning_architecture.md` |
| Phase 1 Details | `P01.md` |
| Phase 2 Details | `P02.md` |
| Phase 3 Details | `P03.md` |
| Phase 4 Details | `P04.md` |
| Phase 5 Details | `P05.md` |
| Phase 6 Details | `P06.md` |
| Phase 7 Details | `P07.md` |
| Phase 8 Details | `P08.md` |
