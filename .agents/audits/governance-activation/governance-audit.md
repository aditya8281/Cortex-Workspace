# CORTEX Governance Activation Audit

**Date:** 2026-06-25
**Scope:** Complete governance system — CLAUDE.md, hooks, commands, skills, settings, workflows
**Goal:** Claude enters repo → knows what CORTEX is, active version, active phase, plan to follow, workflows, reviews, architecture constraints — without repeated human intervention.

---

## Executive Summary

CORTEX has a **comprehensive governance infrastructure** that is **documented but not fully operational**. The system has:

- ✅ 11 governance hooks (all execute, 6/11 pass on current codebase)
- ✅ 7 slash commands (all present, well-structured)
- ✅ 66 skills (functional, but 0 Cortex-specific)
- ✅ 10 workflow definitions (1 fully operational, 3 partial, 6 not automated)
- ✅ Settings file (permissions correct, 1 hook configured)
- ❌ **No active version tracking** — zero components started across all 6 versions
- ❌ **No current state indicator** — Claude cannot determine what to work on
- ❌ **CLAUDE.md was a reference doc, not an execution contract** — FIXED in this audit

**Verdict:** Infrastructure exists. Execution enforcement is weak. The rewrite of CLAUDE.md to include an Entry Protocol and Authority Hierarchy is the critical fix that makes the system self-guiding.

---

## Audit Results by Phase

### Phase 1: Discovery Audit

| Area | Status | Findings |
|------|--------|----------|
| Governance docs | ✅ Comprehensive | CLAUDE.md, AGENTS.md, DESIGN.md, GOVERNANCE.md, WORKFLOWS.md, DEVELOPER_GUIDE.md |
| Source of truth | ✅ Defined | Authority hierarchy: CLAUDE.md > guide.md > AGENTS.md > plans > docs |
| Active state tracking | ❌ Missing | No version has any component started. No ACTIVE.md or STATUS.md file. |
| Plan infrastructure | ✅ Complete | guide.md (constitution), 6 version plans, 18 phase plans, implementation_steps.md |
| Hook infrastructure | ✅ Functional | 11 hooks, runner, shared utils, phase mapping |
| Command infrastructure | ✅ Complete | 7 slash commands, all well-structured |
| Skill infrastructure | ✅ Functional | 66 skills, no manifest, 0 Cortex-specific |
| Settings | ✅ Working | Permissions correct, 1 hook configured |

### Phase 2: CLAUDE.md Rewrite

**Before:** Reference doc with architecture details, commands, patterns. No execution guidance.
**After:** Execution contract with Entry Protocol, Authority Hierarchy, Active State Discovery, Execution Contract.

Key additions:
- **Entry Protocol** — 4-step process Claude must follow on repository entry
- **Authority Hierarchy** — 6-level priority when documents conflict
- **Active Version System** — Points to progress.md files for state tracking
- **Execution Contract** — Before/During/After work rules with completion criteria
- **Architecture Constraints** — Immutable rules extracted from guide.md

### Phase 3: Hook Registration Audit

**File:** `hooks-audit.md`

| Metric | Value |
|--------|-------|
| Hooks registered | 11/11 ✅ |
| Hooks executable | 11/11 ✅ |
| Hooks passing | 6/11 (5 fail on pre-existing codebase issues) |
| Phase mapping complete | ✅ |
| Wired into Claude Code | ❌ Only 1 (impeccable) |

**Critical finding:** Governance hooks run via `make hooks-*` but are NOT enforced by Claude Code's hook system. Agents can skip them.

### Phase 4: Command Registration Audit

**File:** `commands-audit.md`

| Metric | Value |
|--------|-------|
| Commands present | 7/7 ✅ |
| Referenced in CLAUDE.md | 7/7 ✅ |
| Referenced in WORKFLOWS.md | 4/7 |
| Referenced in DEVELOPER_GUIDE.md | 4/7 |
| Overlapping commands | 0 significant |

**Missing commands:** `/project:status` (active state), `/project:audit`, `/project:release`

### Phase 5: Skill Registration Audit

**File:** `skills-audit.md`

| Metric | Value |
|--------|-------|
| Skills present | 66 ✅ |
| Cortex-specific skills | 0/10 planned ❌ |
| Skills with scripts | 6 (brainstorming, caveman-compress, diagnosing-bugs, git-guardrails, subagent-driven-development, ui-ux-pro-max) |
| Manifest/index | ❌ None |
| Duplicate/overlapping | 3 pairs identified |

### Phase 6: Settings Audit

**File:** `settings-audit.md`

| Metric | Value |
|--------|-------|
| settings.local.json | ✅ Correct |
| Permissions | 57 allow rules ✅ |
| Hooks configured | 1 (impeccable) |
| Pre-commit config | ✅ Working |
| Makefile | ✅ 40+ targets |
| HTML entities | ✅ Already correct (false alarm from agent output) |

### Phase 7: Workflow Activation Audit

**File:** `workflow-audit.md`

| Metric | Value |
|--------|-------|
| Workflows defined | 10 |
| Fully operational | 1 (Validation) |
| Partially operational | 3 (Development Lifecycle, Review, Development) |
| Not operational | 6 (Bug-Finding, Refactoring, Release, Documentation, Skill Creation, Skill Evolution) |
| Enforcement via hooks | 5 of 11 stages automated |
| Enforcement via CI | ruff, mypy, pytest, next lint, tsc, vitest, build |

---

## Critical Gaps Identified

### Gap 0: No Active State (FIXED)

**Problem:** Claude entering this repo cannot determine what version is being developed, what phase is active, or what to work on next.

**Fix applied:** CLAUDE.md now includes:
- Entry Protocol with explicit steps to read `guide.md`, `progress.md`, `implementation_steps.md`
- Active version system pointing to `progress.md` files
- Authority hierarchy for document conflicts

### Gap 1: Hooks Not Enforced by Platform

**Problem:** 11 governance hooks exist but only 1 (impeccable) runs via Claude Code's hook system. The rest require manual `make hooks-*` commands.

**Recommendation:** Either:
- (a) Wire completion-gate into Claude Code's PostToolUse hooks, OR
- (b) Add prominent documentation that `make hooks-push` is mandatory (done in CLAUDE.md)

### Gap 2: Zero Cortex-Specific Skills

**Problem:** GOVERNANCE.md lists 10 Cortex-specific skill candidates. None exist. The ecosystem claims to be "skill-driven" but has no domain-specific skills.

**Recommendation:** Create at least `cortex-architecture-audit` and `cortex-health-review` skills.

### Gap 3: No Plan Enforcement

**Problem:** Nothing verifies an agent read the phase plan before implementing. Agents can start coding without knowing the constraints.

**Recommendation:** Add plan-existence check to completion-gate hook, or document in CLAUDE.md (done).

### Gap 4: 6 Workflows Not Operational

**Problem:** Bug-Finding, Refactoring, Release, Documentation, Skill Creation, Skill Evolution are defined but have no automation.

**Recommendation:** Prioritize Bug-Finding and Release automation.

---

## What Claude Can Now Determine on Entry

| Question | Before Audit | After Audit |
|----------|-------------|-------------|
| What is CORTEX? | ✅ CLAUDE.md overview | ✅ CLAUDE.md first line |
| What version is active? | ❌ No indicator | ✅ Entry Protocol → read progress.md |
| What phase is active? | ❌ No indicator | ✅ Entry Protocol → read Phase-N.md |
| What plan to follow? | ❌ Scattered | ✅ Authority Hierarchy → implementation_steps.md |
| What workflows to use? | ⚠️ In WORKFLOWS.md but not linked | ✅ CLAUDE.md "Mandatory Workflow" section |
| What reviews are mandatory? | ⚠️ In CLAUDE.md but buried | ✅ CLAUDE.md "Mandatory Reviews" table |
| What architecture constraints? | ⚠️ In guide.md, scattered | ✅ CLAUDE.md "Architecture Constraints" section |

**Verdict:** All 7 questions now answerable from CLAUDE.md alone, with pointers to detailed docs.

---

## Deliverables

| File | Location | Purpose |
|------|----------|---------|
| governance-audit.md | `.agents/audits/governance-activation/` | This master audit |
| hooks-audit.md | `.agents/audits/governance-activation/` | Hook registration & execution audit |
| commands-audit.md | `.agents/audits/governance-activation/` | Slash command audit |
| skills-audit.md | `.agents/audits/governance-activation/` | Skills inventory & gap analysis |
| settings-audit.md | `.agents/audits/governance-activation/` | Settings & configuration audit |
| workflow-audit.md | `.agents/audits/governance-activation/` | Workflow operational status audit |
| CLAUDE.md (rewritten) | `/CLAUDE.md` | Execution contract with Entry Protocol |

---

## Recommended Priority Actions

| # | Priority | Action | Effort | Impact |
|---|----------|--------|--------|--------|
| 1 | P0 | CLAUDE.md rewrite as execution contract | ✅ DONE | Claude can self-guide on entry |
| 2 | P1 | Test all 11 hooks for execution | ✅ DONE | Verified 6/11 pass, 5 fail on pre-existing issues |
| 3 | P1 | Create `/project:status` command | 30 min | Quick active state discovery |
| 4 | P1 | Wire completion-gate into Claude Code hooks | 30 min | Platform-enforced quality gate |
| 5 | P2 | Create `.agents/skills/INDEX.md` manifest | 30 min | Skill discoverability |
| 6 | P2 | Create `cortex-architecture-audit` skill | 1 hr | Domain-specific quality |
| 7 | P2 | Add git hook to prevent direct commits to main | 30 min | Branch enforcement |
| 8 | P3 | Add frontend pre-commit hooks | 30 min | Frontend quality on commit |
| 9 | P3 | Create remaining Cortex-specific skills | 4 hr | Ecosystem maturity |
| 10 | P3 | Automate Bug-Finding and Release workflows | 4 hr | Workflow operational coverage |

---

## Verification Checklist

Can Claude, on entering this repository, correctly determine:

- [x] **What CORTEX is** — CLAUDE.md line 3: "CORTEX is a local-first machine intelligence layer"
- [x] **What version is active** — Entry Protocol step 1: read progress.md files
- [x] **What phase is active** — Entry Protocol step 1: grep for in_progress
- [x] **What plan to follow** — Authority Hierarchy: guide.md > implementation_steps.md > Phase-N.md
- [x] **What workflows to use** — Mandatory Workflow section: Branch → Skill Discovery → ... → Merge
- [x] **What reviews are mandatory** — Mandatory Reviews table: review, challenge, reflect, architecture, health
- [x] **What architecture constraints exist** — Architecture Constraints section: immutable rules from guide.md

**All 7 questions answerable. Audit goal achieved.**
