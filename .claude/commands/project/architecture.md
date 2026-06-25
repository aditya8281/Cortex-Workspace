# /project:architecture — Architecture Alignment Check

Run before implementing significant new systems or modifying core architecture.

## Instructions

### 1. Read Context

Invoke `cortex-repo-discovery`. Read `docs/ARCHITECTURE.md` completely. Read active version context.

### 2. Understand Proposed Change

Check recent commits, active plans, the user's stated goal.

### 3. Architecture Alignment

- Fits documented system structure?
- Follows service layer pattern?
- Uses correct DB conventions (SQLAlchemy + Alembic)?
- Follows auth model (JWT + cookies, ownership checks)?

### 4. CORTEX Principles

- Privacy-first, compound learning, two-tier trust, graceful degradation, model freedom, living knowledge, version alignment?

### 5. Architecture Drift

Invoke `cortex-architecture-drift` for file placement, drift detection, ADR checks.

### 6. ADR Required When

New technology, architecture pattern change, security policy change, API design decision, DB schema philosophy change, testing strategy change, deployment approach change.

Check `docs/decisions/` for existing ADRs. Recommend creating if none exists.

### 7. Output

```text
## Architecture Alignment: [date]

### Proposed Change
### Architecture Fit: PASS/WARN/FAIL (table per check)
### CORTEX Principles: PASS/WARN/FAIL (table per principle)
### File Placement: PASS/WARN/FAIL
### Architecture Drift: PASS/WARN/FAIL
### ADR Required: YES/NO [title, key decisions]
### Summary: Overall, Issues N, Recommendations N
```
