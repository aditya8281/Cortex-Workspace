# /project:audit — Codebase Audit

Deep code-level scan for runtime errors, dead code, integration issues, broken imports, placeholders, and technical debt.

**Scope:** Code-level analysis. For broad ecosystem health (skills, docs, governance trends), use `/project:health` instead.

## Instructions

### 1. Read Scope

Run `.agents/plans/shared-phases.md#repository-intelligence`.

Read the active phase plan to know what components are in scope.

### 2. Baseline

Run `.agents/plans/shared-phases.md#system-validation`.

### 3. Runtime Errors

Scan for code that will crash at runtime:

- **Imports:** Find any `ImportError` or missing module references. Run:
  ```bash
  python -c "import backend.app.main" 2>&1
  ```
  Check all service files import their dependencies correctly.

- **Singletons:** Verify all global singletons (llm_manager, redis_cache, download_manager) are properly initialized in their modules.

- **API patterns:** Check all endpoints in `backend/app/api/v1/` for:
  - Missing `response_model=` on decorator
  - Missing ownership checks (`resource.user_id == current_user.id`) on user-scoped endpoints
  - Routes not in correct order (specific before parameterized)

### 4. Dead Code

Find functions, classes, or modules never imported or called:

```bash
# Find potentially unused functions
grep -rn "^def \|^class " backend/app/services/ | head -50
```

For each candidate, apply the **UNIQUE CAPABILITIES TEST:**
- Is it imported anywhere? `grep -rn "from.*import.*FunctionName" backend/`
- If not imported, does it provide a capability not covered by any other service?
- If it provides unique capability: KEEP (not dead code)
- If no unique capability and not imported: flag for deletion

### 5. Integration Issues

- **Service chains:** Verify complete dependency chains:
  - `file_watcher_v2` → `indexing_orchestrator` → `incremental_indexer`/`document_indexer`
  - `deletion_pipeline` handles cascade cleanup
  - `cross_file_search` does graph-enriched search
  - `path_index` provides directory tree browsing

- **Mock patches:** Verify all patches in `tests/conftest.py` match actual service imports:
  ```bash
  grep "patch(" tests/conftest.py
  ```
  For each, verify the import path exists in the actual service file.

- **Model imports:** Verify all models are imported in `migrations/env.py` for Alembic autogenerate.

### 6. Placeholders

Scan for incomplete implementations:

```bash
grep -rn "TODO\|FIXME\|HACK\|XXX\|TBD\|NotImplementedError" backend/ frontend/ --include="*.py" --include="*.ts" --include="*.tsx" | head -30
```

Also scan for:
- `pass` in non-trivial functions (functions longer than just `pass`)
- Mock/placeholder return values in production code (e.g., `return []` in a function that should query a database)

### 7. Consistency

- Cross-reference CLAUDE.md claims vs actual codebase (e.g., if CLAUDE.md says "341 tests", verify)
- Check docs/ references are valid (no broken links to files that don't exist)
- Verify migration chain is unbroken:
  ```bash
  make migrate
  ```

## Output

```markdown
## Audit: [date]

### Baseline
Tests: PASS/FAIL (N/N) | Lint: CLEAN/DIRTY

### Runtime Errors
| # | Severity | File:Line | Issue | Fix |
|---|----------|-----------|-------|-----|

### Dead Code
| # | File:Line | Verdict | Reason |
|---|-----------|---------|--------|

### Integration Issues
| # | Severity | Issue | Fix |
|---|----------|-------|-----|

### Placeholders
| # | File:Line | Type | Content |
|---|-----------|------|---------|

### Consistency
| # | Issue | Fix |
|---|-------|-----|

### Summary
- Runtime errors: N
- Dead code candidates: N (N confirmed dead, N retained for unique capability)
- Integration issues: N
- Placeholders: N
- Consistency gaps: N
```
