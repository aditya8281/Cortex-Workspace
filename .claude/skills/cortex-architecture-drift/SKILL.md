# cortex-architecture-drift

Detect divergence between documented architecture and actual codebase.

## When to Use

Before release, after architecture changes, during health check.

## Process

### 1. Check Architecture Principles

For each architecture section in `GUIDE.md` §4 (Daemon, Desktop, Memory, Graph, Retrieval, Agent, Workflow, Plugin, CLI, Ecosystem):

- Is the "current approach" description accurate?
- Is the "final decision" still the intended direction?
- Has implementation diverged from documented design?

### 2. Check ADRs

- Read `docs/decisions/README.md` for ordering
- For each ADR: verify its decision still reflects the codebase
- Mark superseded ADRs
- Identify undocumented decisions needing new ADRs

### 3. Check File Placement

- Models in `backend/app/models/`
- Schemas in `backend/app/schemas/`
- Routers in `backend/app/api/v1/`
- Services in `backend/app/services/`
- Core in `backend/app/core/`
- Agents in `backend/app/agents/`
- Tests in `tests/`
- Migrations in `migrations/versions/`

## Output

Status per section: aligned / warn / drift. Recommendations for each drift found.

## Examples

```
Invoke cortex-architecture-drift before release.
```
