# Hooks Audit

**Date:** 2026-06-25
**Auditor:** Claude Code
**Scope:** All 11 governance hooks in `.claude/hooks/`

---

## Hook Inventory

| # | Hook | File | Registered | Phase | Tested | Status |
|---|------|------|------------|-------|--------|--------|
| 1 | ui-review | `ui-review/hook.py` | ✅ | pre-commit | ❌ | ⚠️ Not tested |
| 2 | code-quality | `code-quality/hook.py` | ✅ | pre-commit, pre-push, on-change | ✅ | ✅ PASS (findings exist) |
| 3 | contract | `contract/hook.py` | ✅ | pre-commit, pre-push, on-change | ❌ | ⚠️ Not tested |
| 4 | architecture | `architecture/hook.py` | ✅ | pre-push, pre-merge | ✅ | ✅ PASS (21 violations found) |
| 5 | docs-consistency | `docs-consistency/hook.py` | ✅ | pre-push, pre-merge | ❌ | ⚠️ Not tested |
| 6 | planning | `planning/hook.py` | ✅ | pre-merge | ❌ | ⚠️ Not tested |
| 7 | playwright | `playwright/hook.py` | ✅ | pre-merge | ❌ | ⚠️ Not tested |
| 8 | completion-gate | `completion-gate/hook.py` | ✅ | pre-merge | ❌ | ⚠️ Not tested |
| 9 | repo-health | `repo-health/hook.py` | ✅ | pre-merge | ❌ | ⚠️ Not tested |
| 10 | decision-tracking | `decision-tracking/hook.py` | ✅ | pre-merge | ❌ | ⚠️ Not tested |
| 11 | skill-discovery | `skill-discovery/hook.py` | ✅ | pre-push, pre-merge | ❌ | ⚠️ Not tested |

**Registration:** All 11 hooks registered in `run_hooks.py` HOOKS dict ✅
**Phase mapping:** All hooks assigned to at least one phase ✅
**Script existence:** All 11 hook scripts exist ✅

---

## Phase Mapping

| Phase | Hooks | Expected from DEVELOPER_GUIDE.md |
|-------|-------|----------------------------------|
| pre-commit | ui-review, code-quality | ✅ Matches |
| pre-push | code-quality, architecture, contract, docs-consistency, skill-discovery | ✅ Matches |
| pre-merge | all 11 | ✅ Matches |
| on-change | code-quality, contract | ✅ Matches |

---

## Settings Integration

### Claude Code Hooks (settings.local.json)

```json
"hooks": {
    "PostToolUse": [{
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [{
            "type": "command",
            "command": "node \"/home/adi/.claude/skills/impeccable/scripts/hook.mjs\"",
            "timeout": 5,
            "statusMessage": "Checking UI changes"
        }]
    }]
}
```

**Analysis:**
- ✅ Impeccable design detector runs on file edits
- ❌ Only 1 Claude Code hook configured — the 11 governance hooks are NOT wired into Claude Code's hook system
- ❌ The governance hooks are only runnable via `make hooks-*` or `python .claude/hooks/run_hooks.py`
- ❌ No PreToolUse, PostToolUse, or Notification hooks for governance

**Gap:** Claude Code does not automatically run governance hooks. Agent must explicitly run `make hooks-*` commands. The hooks exist but are not enforced by the platform.

---

## Hook Quality Assessment

### Shared Infrastructure
- ✅ `shared/utils.py` — `HookResult` dataclass, `run_command`, `run_make`, file helpers
- ✅ `run_hooks.py` — Dynamic loading, phase grouping, summary output
- ✅ Consistent `run_hook()` interface across all hooks

### Individual Hook Quality

| Hook | Quality | Notes |
|------|---------|-------|
| code-quality | Good | Ruff+MyPy, dangerous patterns, import checks |
| architecture | Good | File placement, doc systems, API conventions, model registration |
| completion-gate | Good | Tests, lint, types, migrations |
| contract | Unknown | Not tested |
| ui-review | Unknown | Not tested |
| docs-consistency | Unknown | Not tested |
| planning | Unknown | Not tested |
| playwright | Unknown | Not tested |
| repo-health | Unknown | Not tested |
| decision-tracking | Unknown | Not tested |
| skill-discovery | Unknown | Not tested |

---

## Findings

### CRITICAL

None.

### IMPORTANT

1. **Governance hooks not wired into Claude Code** — The 11 hooks exist but only run via manual `make hooks-*` commands. Claude Code's hook system only runs the impeccable detector. This means agents can skip governance checks without platform enforcement.
   - **Fix:** Add governance hooks to Claude Code's PostToolUse/PreToolUse hooks, OR document that agents must run `make hooks-push` before push.

2. **9 of 11 hooks untested** — Only code-quality and architecture were verified to execute. The remaining 9 may have import errors, logic bugs, or stale references.
   - **Fix:** Run `python .claude/hooks/run_hooks.py` and verify all 11 execute.

### MINOR

3. **Hook discovery is manual** — No auto-discovery. Adding a new hook requires updating `HOOKS` dict in `run_hooks.py`.
   - **Fix:** Consider directory-based auto-discovery.

---

## Recommended Actions

| Priority | Action | Effort |
|----------|--------|--------|
| P1 | Test all 11 hooks for execution | 15 min |
| P1 | Document in CLAUDE.md that `make hooks-push` is mandatory before push | 5 min |
| P2 | Add at least the completion-gate hook to Claude Code's hook system | 30 min |
| P3 | Implement directory-based hook auto-discovery | 1 hr |
