# Shared Execution Phases

This document defines reusable phases that multiple commands reference. Each phase delegates to a dedicated skill in `.agents/skills/`.

**Purpose:** Commands orchestrate; skills contain intelligence. Update a skill, and every referencing command stays consistent.

---

## Phase: Repository Intelligence

Used by: `/project:develop` S1, `/project:prompt` S0-1, `/project:audit` S1, `/project:feature-gap` S1, `/project:release` S1

Invoke `cortex-repository-intelligence` to discover git state, active version, repo structure, and test baseline.

Ensure `cortex-repo-discovery` has run first (repo root found and cwd set).

---

## Phase: Planning Ecosystem Load

Used by: `/project:enhance_plan` S0, `/project:feature-gap` S1, `/project:release` S1, `/project:update` P0.1

Invoke `cortex-planning-ecosystem` to load guide.md, implementation_steps.md, roadmap, version plans, and progress tracking.

---

## Phase: System Validation

Used by: `/project:cortex` P4, `/project:verify`, `/project:audit` S2, `/project:release` S2

Invoke `cortex-system-validation` to run tests, lint, format check, hooks, and migrations.

**Block merge on any FAIL.**

---

## Phase: Documentation Consistency Check

Used by: `/project:cortex` P5, `/project:reflect` (docs section), `/project:enhance_plan` S3, `/project:release` S4

Invoke `cortex-documentation-consistency` to cross-reference every doc against current implementation.

---

## Phase: Engineering Quality Review

Used by: `/project:cortex` P5, `/project:review`

Invoke `cortex-engineering-review` to check correctness, API patterns, code quality, and testing.

**Block push on any P0 findings.**

---

## Phase: Architecture Drift Detection

Used by: `/project:cortex` P5, `/project:architecture`, `/project:enhance_plan` S3

Invoke `cortex-architecture-drift` to verify guide.md sections and ADRs against current codebase.

---

## Phase: Adversarial Challenge

Used by: `/project:cortex` P5, `/project:challenge`, `/project:update` P5

Invoke `cortex-adversarial-challenge` to stress-test plans/specs/implementations for risks, edge cases, assumptions, and principle alignment.

Challenges are advisory — they inform, not block.

---

## Phase: Post-Completion Reflection

Used by: `/project:cortex` P6, `/project:reflect`, `/project:develop` S5

Invoke `cortex-post-reflection` for systematic analysis across quality, redundancy, automation, skill opportunities, docs, tech debt, tests, consistency, and regression risk.

---

## Phase: Repository Cleanup

Used by: `/project:cortex` P7, `/project:develop` (post-execution)

Invoke `cortex-repo-cleanup` to remove temporary files, dead code, and ensure only intentional changes remain.

---

## Phase: Version Integration Check

Used by: `/project:cortex` P8, `/project:release`

Invoke `cortex-version-integration` to verify pre-merge gate and run merge verification.

---

## Phase: Repository Health Scan

Used by: `/project:health`, `/project:improve`

Invoke `cortex-repo-health-scan` to check hook health, skill health, tech debt hotspots, and documentation freshness.
