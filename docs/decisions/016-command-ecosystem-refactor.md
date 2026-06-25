# ADR 016: Command Ecosystem Architectural Refactor

**Date:** 2026-06-25
**Status:** Accepted
**Impact:** All 16 commands, `.agents/plans/shared-phases.md`, `docs/WORKFLOWS.md`, `CLAUDE.md`

## Context

The Cortex command ecosystem grew organically across multiple sessions. Each command was independently authored, leading to:

1. **Massive duplication** — Repository Intelligence phase was duplicated verbatim in 8+ commands (cortex, develop, prompt, audit, feature-gap, release, update, enhance_plan)
2. **No clear hierarchy** — All 16 commands appeared flat with no orchestrator layer
3. **Inconsistent scoping** — Some commands duelled for the same job (e.g., what distinguishes cortex from develop wasn't documented)
4. **Hard to maintain** — Updating Repository Intelligence meant touching 8 files instead of 1
5. **No evolution pathway** — No command existed to take a raw idea through to approved plan; every command assumed the user already had a clear spec

## Decision

### 1. Create 3-Tier Orchestrator Hierarchy

Commands are now classified into three tiers:

| Tier | Commands | Responsibility |
|------|----------|----------------|
| **Orchestrator** | `update`, `enhance_plan`, `develop` | Determine what work to do, compose specialist commands, never implement directly |
| **Autonomous** | `cortex` | End-to-end implementation loop after scope is defined |
| **Specialist** | All others | Single-responsibility analysis/generation tasks |

### 2. Extract Shared Phases

Created `.agents/plans/shared-phases.md` with 11 reusable execution phases:

- **Repository Intelligence** — Build repo understanding (was in 8 commands)
- **Planning Ecosystem Load** — Read plans/roadmap/ADRs (was in 6 commands)
- **System Validation** — Run tests/lint/hooks (was in 5 commands)
- **Documentation Consistency Check** — Cross-reference docs vs implementation
- **Engineering Quality Review** — Architecture, performance, security, maintainability
- **Architecture Drift Detection** — File placement, ownership, layer boundaries
- **Adversarial Challenge** — Refute findings before reporting
- **Post-Completion Reflection** — Full reflection framework
- **Repository Cleanup** — Temp files, dead code, stale references
- **Version Integration Check** — Commit quality, merge readiness
- **Repository Health Scan** — Dead code, duplicates, drift, placeholders, security

### 3. Create update.md — Project Evolution Orchestrator

The top-level orchestrator with 8 phases:
1. Repository Intelligence + Classification
2. Exploration + Skill Synthesis
3. Specification (16-section module template)
4. Repository Impact Analysis
5. Planning Ecosystem Integration
6. Adversarial Review
7. Approval Gate
8. Development Handoff

Key design decisions:
- **Skill routing table** — Maps request categories (feature, architecture, refactor, etc.) to relevant brainstorming skills
- **Spec scaling** — Automatically adjusts spec detail to request complexity (simple/medium/complex/vision)
- **Never-implement gates** — 4 explicit checkpoints preventing premature implementation
- **Ecosystem impact analysis** — Table-based analysis of every planning artifact

### 4. Create enhance_plan.md — Planning Ecosystem Improver

A 7-phase planning ecosystem command with 4 distinct drift analyses:
1. **Implementation drift** — What's been built vs what's documented
2. **Planning drift** — Plans contain incomplete items, stale estimates, outdated blockers
3. **Architecture drift** — Files don't match where architecture says they should be
4. **Vision drift** — Catches product vision contamination (flagged for user, never auto-changed)

Key design rule: **Never change product vision** — any vision drift found is escalated for user decision.

### 5. Refactor 6 Existing Commands

Replaced inline duplicated phases with references to shared phases:

| Command | Lines Before | Lines After | Savings |
|---------|-------------|-------------|---------|
| cortex.md | ~422 | ~200 | ~222 |
| develop.md | ~330 | ~294 | ~36 |
| prompt.md | ~370 | ~346 | ~24 |
| audit.md | ~170 | ~156 | ~14 |
| feature-gap.md | ~125 | ~116 | ~9 |
| release.md | ~95 | ~86 | ~9 |

Total: ~314 lines of duplicated instructions removed.

### 6. Update Ecosystem Documentation

- **WORKFLOWS.md** — Added section 1 (Command Ecosystem Hierarchy) with ASCII hierarchy diagram, orchestrator/specialist tables, shared phase list. Renumbered sections 2-10 → 3-11.
- **CLAUDE.md** — Updated Strategic Commands table with 3-tier grouping (Orchestrators, Autonomous, Specialist).
- **CLAUDE.md** — Added `enhance_plan` and `update` to command table.

## Consequences

### Positive

- **Single source of truth** for Repository Intelligence — update one file, all commands benefit
- **Clear role separation** — orchestrators compose specialists, never duplicate them
- **Lower cognitive load** — new commands reference shared phases rather than reinventing them
- **Easier onboarding** — agents see "run Repository Intelligence" instead of 30 lines of bash
- **Evolution path** — ideas flow `update → enhance_plan → develop → cortex`, each stage adding precision
- **~314 lines less duplication** in command files

### Negative

- **Indirection** — command readers must jump to shared-phases.md for phase details
- **Shared file coupling** — changes to shared phases affect all commands that reference them (mitigated by careful phase design)
- **New commands must know** to reference shared phases rather than duplicating

### Migration

All existing commands remain functional. No breaking changes. The refactored commands (`cortex`, `develop`, `prompt`, `audit`, `feature-gap`, `release`) replaced duplicated instructions with references but preserved all unique logic.

Files modified: 12
Files created: 4 (shared-phases.md, update.md, enhance_plan.md, this ADR)
Files not yet updated: ROADMAP.md (phase names detected as stale during research — deferred)
