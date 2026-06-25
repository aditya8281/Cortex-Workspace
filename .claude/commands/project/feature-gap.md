# /project:feature-gap — Roadmap vs Codebase Gap Analysis

Cross-reference roadmap/phase plans against the actual codebase. Find what's planned but not implemented.

**Scope:** Missing/planned work. For issues in existing code, use `/project:audit` instead.

## Instructions

### 1. Read the Roadmap

Run `.agents/plans/shared-phases.md#repository-intelligence`.
Run `.agents/plans/shared-phases.md#planning-ecosystem-load`.

### 2. Scan the Codebase

```bash
# Backend services
ls backend/app/services/

# Backend API endpoints
ls backend/app/api/v1/

# Backend models
ls backend/app/models/

# Frontend features
ls frontend/src/app/
ls frontend/src/components/
```

### 3. Cross-Reference

For each component in the phase plan:

| Check | How |
|-------|-----|
| Service exists? | Does `backend/app/services/<name>.py` exist? |
| Service complete? | Is it more than a stub? Does it have real logic? |
| API endpoint exists? | Is it registered in `backend/app/api/v1/`? |
| Model exists? | Is it in `backend/app/models/`? |
| Migration exists? | Is there a migration for it in `migrations/versions/`? |
| Tests exist? | Is there a test file in `tests/`? |
| Frontend support? | Is there UI for it in `frontend/src/`? |
| Documented? | Is it in the relevant docs/ file? |

### 4. Classify Gaps

For each planned component, classify:

- **Complete** — fully implemented and tested
- **Partial** — started but incomplete
- **Stubbed** — scaffolded but no real implementation
- **Missing** — not started at all

### 5. Estimate Effort

For non-complete components, estimate effort:
- **XS** — a few hours, single file
- **S** — half a day, 1-2 files
- **M** — 1-2 days, 3-5 files
- **L** — 3-5 days, 5-10 files
- **XL** — 1+ weeks, cross-cutting

### 6. Prioritize

Order gaps by:
1. Blocks downstream work (dependency)
2. High impact, low effort (quick wins)
3. High impact, high effort (major features)
4. Low impact (nice-to-haves)

## Output

```markdown
## Feature Gap: [date]

### Version: VX — Phase N: [name]

| Component | Planned | Exists | Status | Tests | Effort |
|-----------|---------|--------|--------|-------|--------|
| [name] | Yes | Yes/No | Complete/Partial/Stubbed/Missing | N/N | XS/S/M/L/XL |

### Summary
- Complete: N components
- Partial: N components
- Stubbed: N components
- Missing: N components
- Total effort: XS/S/M/L/XL

### Recommended Priority
1. [Component] — [reason]
2. [Component] — [reason]

### Quick Wins (high impact, low effort)
- [Component] — [effort estimate]
```
