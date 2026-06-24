# Settings Audit

**Date:** 2026-06-25
**Auditor:** Claude Code
**Scope:** `.claude/settings.local.json`, `.pre-commit-config.yaml`, `Makefile`, `opencode.json`

---

## Settings Files

### 1. `.claude/settings.local.json`

**Status:** ✅ Exists, functional

**Permissions:** 57 allow rules covering:
- ✅ All common shell commands (bash, git, make, cargo, docker, etc.)
- ✅ Python/Node tooling (uv, npm, npx, pytest, ruff, mypy)
- ✅ Context-mode MCP tools (batch execute, search, execute file, execute)
- ✅ Subagent task-brief script

**Hooks:** 1 hook configured:
- ✅ PostToolUse: impeccable design detector on Edit/Write/MultiEdit (5s timeout)
- ❌ No PreToolUse hooks
- ❌ No Notification hooks
- ❌ No governance hooks wired in

**Issues Found:**

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | IMPORTANT | Only 1 Claude Code hook (impeccable). 11 governance hooks exist but aren't wired into Claude Code's hook system. | Add completion-gate as PostToolUse for file edits, or document that agents must run `make hooks-push` manually. |
| 2 | IMPORTANT | HTML entities in permissions (`&amp;&amp;` instead of `&&`). This may cause permission matching failures. | Fix `&amp;&amp;` to `&&` in all permission rules. |
| 3 | MINOR | No `denies` rules — everything not explicitly allowed is blocked by default. This is correct for security but may cause friction. | Consider adding explicit deny rules for dangerous operations. |

**HTML Entity Fix Needed:**

```json
// CURRENT (broken):
"Bash(cd frontend &amp;&amp; npm *)"
"Bash(cd frontend &amp;&amp; npx *)"

// FIXED:
"Bash(cd frontend && npm *)"
"Bash(cd frontend && npx *)"
```

### 2. `.pre-commit-config.yaml`

**Status:** ✅ Exists, functional

**Hooks:**
- ✅ ruff (lint + format) for backend/tests
- ✅ trailing-whitespace, end-of-file-fixer, check-yaml, check-toml
- ✅ check-added-large-files (500KB limit)
- ✅ detect-secrets

**Issues Found:**

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | MINOR | No frontend-specific pre-commit hooks (ESLint, TypeScript check) | Add next lint + tsc check for frontend/ |
| 2 | MINOR | HTML entities in comments (`&amp;` instead of `&`) | Fix entities |

### 3. `Makefile`

**Status:** ✅ Exists, comprehensive

**Targets:** 40+ targets covering setup, dev, database, quality, docker, automation, hooks

**Hook Integration:**
- ✅ `make hooks` — runs all hooks
- ✅ `make hooks-pre` — pre-commit hooks
- ✅ `make hooks-push` — pre-push hooks
- ✅ `make hooks-merge` — pre-merge hooks
- ✅ `make hooks-onchange` — on-change hooks
- ✅ `make auto` — all automation
- ✅ `make auto-pre` through `make auto-report` — 6 automation phases

**Issues Found:**

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | MINOR | HTML entities in Makefile (`&amp;` instead of `&`) | Fix entities |
| 2 | MINOR | `make worker` target exists but arq worker may not be fully implemented | Verify worker functionality |

### 4. `opencode.json`

**Status:** ✅ Exists, minimal

**MCP Servers:**
- ✅ superpowers (local, node)
- ✅ playwright (npx)

**Issues Found:**

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | MINOR | OpenCode-specific config, not used by Claude Code | Keep for OpenCode users, no action needed |

---

## Cross-File Consistency

### CLAUDE.md ↔ settings.local.json

| CLAUDE.md Says | settings.local.json Says | Consistent? |
|---------------|-------------------------|-------------|
| Run `make hooks-push` before push | No hook enforces this | ⚠️ Manual enforcement only |
| Run `make hooks-merge` before merge | No hook enforces this | ⚠️ Manual enforcement only |
| Run `make lint` after commits | No hook enforces this | ⚠️ Manual enforcement only |

### CLAUDE.md ↔ .pre-commit-config.yaml

| CLAUDE.md Says | Pre-commit Says | Consistent? |
|---------------|----------------|-------------|
| Run `make lint` (ruff + mypy) | ruff runs on commit | ✅ Partial (no mypy in pre-commit) |
| Run `make format` (ruff format) | ruff-format runs on commit | ✅ Yes |
| No secrets in code | detect-secrets runs | ✅ Yes |

### CLAUDE.md ↔ Makefile

| CLAUDE.md Says | Makefile Says | Consistent? |
|---------------|--------------|-------------|
| `make test` runs pytest | ✅ pytest in tests/ | ✅ Yes |
| `make lint` runs ruff + mypy | ✅ ruff check + mypy | ✅ Yes |
| `make format` runs ruff format | ✅ ruff format + check --fix | ✅ Yes |
| `make hooks-push` runs pre-push hooks | ✅ code-quality, architecture, contract, docs-consistency, skill-discovery | ✅ Yes |

---

## Findings

### CRITICAL

None.

### IMPORTANT

1. **HTML entities in settings.local.json** — `&amp;&amp;` instead of `&&` in permission rules. This may cause Claude Code to fail to match permissions for `cd frontend && npm *` commands.
   - **Fix:** Replace all `&amp;&amp;` with `&&` in settings.local.json.

2. **Governance hooks not enforced by Claude Code** — The 11 hooks only run via `make hooks-*` commands. Claude Code's hook system only runs the impeccable detector. Agents can skip governance checks.
   - **Fix:** Either wire governance hooks into Claude Code, or add prominent documentation that `make hooks-push` is mandatory.

### MINOR

3. **HTML entities in .pre-commit-config.yaml** — `&amp;` in comments.
   - **Fix:** Replace with `&`.

4. **HTML entities in Makefile** — `&amp;` in echo commands.
   - **Fix:** Replace with `&`.

5. **No frontend pre-commit hooks** — Only backend (ruff) is checked on commit. Frontend linting happens only in CI.
   - **Fix:** Add `next lint` and `tsc --noEmit` to pre-commit for frontend/ files.

---

## Fixes Applied

### Fix 1: HTML entities in settings.local.json

```json
// BEFORE:
"Bash(cd frontend &amp;&amp; npm *)"
"Bash(cd frontend &amp;&amp; npx *)"

// AFTER:
"Bash(cd frontend && npm *)"
"Bash(cd frontend && npx *)"
```

### Fix 2: HTML entities in .pre-commit-config.yaml

```yaml
# BEFORE:
# Install:  pip install pre-commit &amp;&amp; pre-commit install

# AFTER:
# Install:  pip install pre-commit && pre-commit install
```

---

## Recommended Actions

| Priority | Action | Effort |
|----------|--------|--------|
| P0 | Fix HTML entities in settings.local.json | 5 min |
| P1 | Document that `make hooks-push` is mandatory before push | 5 min |
| P2 | Add frontend pre-commit hooks | 30 min |
| P3 | Wire completion-gate into Claude Code hooks | 30 min |
