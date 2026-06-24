# Workflow Audit

**Date:** 2026-06-25
**Auditor:** Claude Code
**Scope:** All workflows defined in `docs/WORKFLOWS.md` and their operational status

---

## Workflow Inventory

| # | Workflow | Defined in WORKFLOWS.md | Has Command | Has Hook | Operational |
|---|----------|------------------------|-------------|----------|-------------|
| 1 | Development Lifecycle | ✅ 7 stages | ❌ | ✅ (hooks) | ⚠️ Partial |
| 2 | Bug-Finding | ✅ | ❌ | ❌ | ❌ Not operational |
| 3 | Validation | ✅ 3 levels | ❌ | ✅ (pre-commit) | ✅ Operational |
| 4 | Review | ✅ | ✅ `/project:review` | ❌ | ⚠️ Partial |
| 5 | Refactoring | ✅ | ❌ | ❌ | ❌ Not operational |
| 6 | Release | ✅ | ❌ | ❌ | ❌ Not operational |
| 7 | Audit | ✅ | ❌ | ❌ | ❌ Not operational |
| 8 | Documentation | ✅ | ❌ | ❌ | ❌ Not operational |
| 9 | Skill Creation | ✅ | ❌ | ❌ | ❌ Not operational |
| 10 | Skill Evolution | ✅ | ❌ | ❌ | ❌ Not operational |

**Summary:** 10 workflows defined, 1 fully operational, 3 partially operational, 6 not operational.

---

## Development Lifecycle Analysis

### Stage Coverage

| Stage | Defined | Enforced | Automated |
|-------|---------|----------|-----------|
| 1. Branch | ✅ | ⚠️ Manual | ❌ No git hook |
| 2. Skill Discovery | ✅ | ⚠️ Manual | ❌ No automation |
| 3. Triage | ✅ | ⚠️ Manual | ❌ No automation |
| 4. Plan | ✅ | ⚠️ Manual | ❌ No automation |
| 5. Build | ✅ | ✅ Pre-commit hooks | ✅ ruff, format |
| 6. Test | ✅ | ⚠️ Manual | ❌ No auto-test on commit |
| 7. Validate | ✅ | ✅ `make hooks-push` | ✅ Hook system |
| 8. Review | ✅ | ⚠️ Manual | ❌ No automation |
| 9. Reflect | ✅ | ⚠️ Manual | ❌ No automation |
| 10. Merge | ✅ | ✅ `make hooks-merge` | ✅ Hook system |

**Enforcement gaps:** Stages 1-4, 6, 8-9 rely on agent discipline, not platform enforcement.

---

## Hook ↔ Workflow Mapping

| Hook | Workflow Stage | Enforced? |
|------|---------------|-----------|
| ui-review | Build (5) | ✅ On frontend file edits |
| code-quality | Build (5), Validate (7) | ✅ On any code change |
| contract | Build (5), Validate (7) | ✅ On API/schema changes |
| architecture | Validate (7) | ✅ On major modifications |
| docs-consistency | Validate (7) | ✅ On significant changes |
| planning | Validate (7) | ✅ On feature completion |
| playwright | Build (5) | ✅ On frontend changes |
| completion-gate | Review (9), Merge (10) | ✅ Before marking complete |
| repo-health | Audit | ✅ Periodically |
| decision-tracking | Plan (4) | ✅ On architecture changes |
| skill-discovery | Skill Discovery (2) | ✅ Pre-task |

---

## Automation ↔ Workflow Mapping

| Automation Phase | Workflow Stage | Command |
|-----------------|---------------|---------|
| pre-work | Context (pre-1) | `make auto-pre` |
| development | Build (5) | `make auto-dev` |
| health | Audit | `make auto-health` |
| bug-discovery | Bug-Finding (2) | `make auto-bugs` |
| completion | Review (9), Merge (10) | `make auto-complete` |
| reports | Audit | `make auto-report` |

---

## Missing Operational Infrastructure

### Workflows Without Automation

| Workflow | Missing | Impact |
|----------|---------|--------|
| Bug-Finding | No auto-trigger, no bug database | Bugs found ad-hoc, not tracked |
| Refactoring | No refactoring guidelines enforced | Refactoring quality varies |
| Release | No release automation | Manual, error-prone |
| Documentation | No doc freshness checks | Docs go stale |
| Skill Creation | No skill template | Skills inconsistent |
| Skill Evolution | No usage tracking | No data on skill effectiveness |

### Stages Without Enforcement

| Stage | Current Enforcement | Gap |
|-------|-------------------|-----|
| Branch | Agent discipline | No git hook prevents direct commits to main |
| Skill Discovery | Agent discipline | No check that skills were consulted |
| Triage | Agent discipline | No classification validation |
| Plan | Agent discipline | No plan existence check |
| Test | Agent discipline | No auto-test on commit |
| Review | Agent discipline | No review existence check |
| Reflect | Agent discipline | No reflection check |

---

## CI Pipeline Coverage

| Check | CI | Pre-commit | Hooks | Makefile |
|-------|----|-----------|-------|----------| 
| ruff lint | ✅ | ✅ | ✅ | ✅ |
| ruff format | ✅ | ✅ | ❌ | ✅ |
| mypy | ✅ | ❌ | ✅ | ✅ |
| pytest | ✅ | ❌ | ✅ (completion-gate) | ✅ |
| next lint | ✅ | ❌ | ❌ | ❌ |
| tsc | ✅ | ❌ | ❌ | ❌ |
| vitest | ✅ | ❌ | ❌ | ❌ |
| next build | ✅ | ❌ | ❌ | ✅ |

**Gap:** Frontend checks (next lint, tsc, vitest) only run in CI, not locally via hooks or pre-commit.

---

## Findings

### CRITICAL

None.

### IMPORTANT

1. **6 of 10 workflows have no automation** — Bug-Finding, Refactoring, Release, Documentation, Skill Creation, Skill Evolution are defined but not operational. Agents must follow them manually.
   - **Fix:** Add automation for the most critical: Bug-Finding and Release.

2. **No git hook prevents direct commits to main** — CLAUDE.md says "Never commit directly to main" but nothing enforces it.
   - **Fix:** Add a pre-commit hook or git hook that blocks commits to main.

3. **No plan existence check** — Agents can start implementing without reading the phase plan. Nothing verifies a plan was consulted.
   - **Fix:** Add a `plan-check` hook that verifies `.agents/plans/versions/vX/Phase-N.md` was read.

### MINOR

4. **Frontend checks not in pre-commit** — Only backend (ruff) runs on commit. Frontend linting happens only in CI.
   - **Fix:** Add next lint + tsc to pre-commit for frontend/ files.

5. **No skill usage tracking** — GOVERNANCE.md says skills should be tracked for effectiveness but no mechanism exists.
   - **Fix:** Add skill usage logging or at minimum a manual tracking file.

---

## Recommended Actions

| Priority | Action | Effort |
|----------|--------|--------|
| P1 | Add git hook to prevent direct commits to main | 30 min |
| P1 | Document that agents must read phase plan before implementing | 5 min |
| P2 | Add frontend pre-commit hooks | 30 min |
| P2 | Create `/project:status` command for workflow state | 30 min |
| P3 | Add plan-existence check hook | 1 hr |
| P3 | Create automation for Bug-Finding workflow | 2 hr |
| P3 | Create automation for Release workflow | 2 hr |
