# /project:audit — Codebase Audit

Deep code-level scan for runtime errors, dead code, integration issues, broken imports, placeholders, and technical debt.

**Scope:** Code-level analysis. For broad ecosystem health (skills, docs, governance), use `/project:health` instead.

## Instructions

### 1. Read Scope

Invoke `cortex-repo-discovery` then `cortex-repository-intelligence`. Invoke `cortex-planning-ecosystem`.

Read the active phase plan to know what components are in scope.

### 2. Baseline

Invoke `cortex-system-validation`.

### 3. Runtime Errors

Scan for code that will crash at runtime:

- **Imports:** Find missing module references. Run `python -c "import backend.app.main"`. Check all service files import dependencies correctly.
- **Singletons:** Verify global singletons (llm_manager, redis_cache, download_manager) are properly initialized.
- **API patterns:** Check all endpoints for missing `response_model=`, missing ownership checks, wrong route order.

### 4. Dead Code

Find functions/classes/modules never imported or called. For each candidate, apply the **UNIQUE CAPABILITIES TEST:** Is it imported anywhere? If not, does it provide a capability not covered elsewhere? If unique → KEEP. If no unique capability and not imported → flag for deletion.

### 5. Integration Issues

- **Service chains:** Verify dependency chains (file_watcher_v2 → indexing_orchestrator → incremental_indexer, etc.)
- **Mock patches:** Verify all patches in `tests/conftest.py` match actual service imports.
- **Model imports:** Verify all models imported in `migrations/env.py` for Alembic autogenerate.

### 6. Placeholders

Scan for TODO, FIXME, HACK, XXX, TBD, NotImplementedError, bare `pass` in non-trivial functions, mock return values in production code.

### 7. Consistency

- Cross-reference CLAUDE.md claims vs actual codebase
- Check docs/ references are valid
- Verify migration chain: `make migrate`

## Output

```markdown
## Audit: [date]

### Baseline (Tests/Lint)
### Runtime Errors
| # | Severity | File:Line | Issue | Fix |
### Dead Code
| # | File:Line | Verdict | Reason |
### Integration Issues
| # | Severity | Issue | Fix |
### Placeholders
| # | File:Line | Type | Content |
### Consistency
| # | Issue | Fix |
### Summary
Runtime errors: N, Dead code: N, Integration issues: N, Placeholders: N, Consistency gaps: N
```
