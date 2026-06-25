# /project:verify — Verification Suite

Run the full verification pipeline and report pass/fail. Fast, focused, no analysis — just automated checks.

**Scope:** Automated pass/fail checks. For code quality analysis and pattern review, use `/project:review` instead.

## Instructions

### 1. Backend Tests

```bash
make test
```

Report: pass/fail, total count, any failures with file:line.

### 2. Frontend Tests (if frontend exists)

```bash
if [ -f frontend/package.json ]; then cd frontend && npm test; else echo "No frontend directory — skipping"; fi
```

Report: pass/fail, total count, any failures.

### 3. Lint

```bash
make lint
```

Report: pass/fail, any warnings or errors.

### 4. Format

```bash
make format --check
```

Report: pass/fail, list files needing format if any.

### 5. Build (if frontend exists)

```bash
if [ -f frontend/package.json ]; then cd frontend && npm run build; else echo "No frontend directory — skipping"; fi
```

Report: pass/fail, any errors.

### 6. Hooks

```bash
uv run python .claude/hooks/run_hooks.py
```

Report: pass/fail per hook.

### 7. Migrations

```bash
make migrate
```

Report: pass/fail, any pending migrations.

## Output

```markdown
## Verification: [date]

| Check | Status | Details |
|-------|--------|---------|
| Backend tests | ✅/❌ N/N | |
| Frontend tests | ✅/❌ N/N | |
| Lint | ✅/❌ | |
| Format | ✅/❌ | [files if failing] |
| Build | ✅/❌ | |
| Hooks | ✅/❌ N/N | |
| Migrations | ✅/❌ | |

### Verdict: PASS / FAIL
```

**Block merge on any FAIL.**
