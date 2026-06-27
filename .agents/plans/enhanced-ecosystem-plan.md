# CORTEX Development Ecosystem Enhancement Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the existing command/skill ecosystem into a plan-oriented development autopilot that reads version plans, executes phases automatically, tracks progress, and chains phases together.

**Architecture:** Commands are thin orchestrators that invoke shared skills. Skills contain reusable intelligence. Every command starts with discovery (repo root, git state, active version), then delegates to skills for the actual work. The new `cortex-phase-executor` skill is the core engine — it reads a phase plan, executes each task, validates, and marks progress.

**Tech Stack:** Claude Code commands (.md), Claude Code skills (SKILL.md), shared-phases.md, progress.md files per version.

---

## Quick Map — Automated Plan-Oriented Development

```
START: /project:start
  │
  ├─→ Discovery (cortex-repo-discovery + cortex-repository-intelligence)
  │     ├─ Find repo root
  │     ├─ Read git state (branch, recent commits, uncommitted work)
  │     ├─ Read IMPLEMENTATION_STEPS.md → find active version
  │     └─ Read active version OVERVIEW.md → find next incomplete phase
  │
  ├─→ Display: "Active: v1.02 P03 — Agent System Hardening. Ready to execute?"
  │
  └─→ /project:cortex (auto-invoked)
        │
        ├─ P0: Discovery (already done by /project:start)
        ├─ P1: Read phase plan (P03.md) → parse tasks
        ├─ P2: Branch (feat/agent-system-hardening)
        ├─ P3: Execute tasks sequentially
        │     ├─ Task 1: Write test → Implement → Verify → Commit
        │     ├─ Task 2: Write test → Implement → Verify → Commit
        │     ├─ ...
        │     └─ Task N: Write test → Implement → Verify → Commit
        ├─ P4: Run full validation (cortex-system-validation)
        ├─ P5: Engineering review (cortex-engineering-review)
        ├─ P6: Update progress.md (mark P03 complete)
        ├─ P7: Commit & merge
        └─ P8: "Phase complete. Next: P04 — MCP Integration. Run /project:next"

CHAIN: /project:next
  │
  ├─→ Read progress.md → find next incomplete phase
  ├─→ If phase exists: auto-invoke /project:cortex with that phase
  └─→ If version complete: "v1.02 complete. Start v1.03? /project:start v1.03"
```

---

## Command Map

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:start` | Quick start — show current state, begin work | Start of session, after break |
| `/project:cortex` | Execute a phase (full implementation cycle) | After /project:start or /project:next |
| `/project:next` | Auto-detect and execute next phase | After completing a phase |
| `/project:develop` | Strategic planning — decide what to work on | When unsure what's next |
| `/project:phase` | Execute a specific phase by name | Manual phase selection |
| `/project:review` | Code quality review | Before push |
| `/project:verify` | Automated verification | Before merge |
| `/project:release` | Release readiness | Before release |

---

## Global Constraints

- All commands start with `cortex-repo-discovery` (find repo root)
- All commands reference GUIDE.md for architecture principles
- All commands reference IMPLEMENTATION_STEPS.md for version/phase context
- Phase execution follows TDD: test first, implement, verify, commit
- Progress tracking via per-version progress.md files
- No source code modification without tests
- Every phase ends with validation (make test, make lint)

---

## Task 1: Create /project:start Command

**Files:**
- Create: `.claude/commands/project/start.md`

**Interfaces:**
- Consumes: cortex-repo-discovery, cortex-repository-intelligence, cortex-planning-ecosystem
- Produces: Active version/phase display, auto-invocation of /project:cortex

- [ ] **Step 1: Write the /project:start command**

```markdown
# /project:start — Quick Start

Read current state and begin development.

## Instructions

### 1. Discovery

Invoke `cortex-repo-discovery`.
Invoke `cortex-repository-intelligence`.

### 2. Find Active Version

Read `.agents/plans/IMPLEMENTATION_STEPS.md`.

Find the first version where progress.md shows incomplete phases.

If no version is active, start with v1.01.

### 3. Find Next Phase

Read the active version's progress.md.

Find the first phase with status "Not started".

### 4. Display Status

Show:
```
## CORTEX Development Status

**Branch:** <current branch>
**Active Version:** vX.XX — <name>
**Next Phase:** P0X — <phase name>
**Phases Complete:** N/M
**Estimated Duration:** X-Y hours

Ready to execute? Run /project:cortex
```

### 5. Auto-Execute (if user confirms)

If user says "yes" or "go", auto-invoke /project:cortex with the active version and phase.
```

- [ ] **Step 2: Test the command**

Run: Invoke `/project:start` and verify it displays the correct status.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/start.md
git commit -m "feat: add /project:start command for quick development entry"
```

---

## Task 2: Create cortex-phase-executor Skill

**Files:**
- Create: `.claude/skills/cortex-phase-executor/SKILL.md`

**Interfaces:**
- Consumes: Phase plan file (P01.md-Pxx.md), progress.md
- Produces: Implemented code, tests, updated progress.md

- [ ] **Step 1: Write the skill**

```markdown
# cortex-phase-executor

Execute a single phase from a version plan. Reads the phase file, executes each task sequentially, validates, and marks progress.

## When to Use

When invoking /project:cortex, /project:next, or /project:phase. This is the core execution engine.

## Process

### 1. Load Phase Context

Read the phase plan file (e.g., `.agents/plans/versions/v1.02/P03.md`).

Parse:
- Phase objective
- Implementation tasks (Task 1 through Task N)
- Testing strategy
- Validation steps
- Definition of Done

### 2. Execute Tasks Sequentially

For each task in the phase plan:

#### 2a. Read Task Requirements
- Files to create/modify
- Interfaces (consumes/produces)
- Test criteria

#### 2b. TDD Cycle
1. Write the failing test
2. Run test to verify it fails
3. Implement the minimal code
4. Run test to verify it passes
5. Commit with descriptive message

#### 2c. Task Complete
- All tests passing
- Code implements the spec
- Commit created

### 3. Phase Validation

After all tasks complete:

```bash
make test
make lint
make format
```

If any check fails, fix before proceeding.

### 4. Update Progress

Read the version's progress.md.

Update the phase status from "Not started" to "Completed".

Set the completion timestamp.

### 5. Report

Output:
```
## Phase Complete: P0X — <name>

**Tasks Completed:** N/N
**Tests:** X passing
**Duration:** Xh Ym
**Next Phase:** P0X+1 — <name>

Run /project:next to continue.
```

## Error Handling

If a task fails:
1. Report the error
2. Show the failing test/command
3. Suggest fix
4. Wait for user confirmation before retrying

If validation fails:
1. Show which checks failed
2. Fix the issues
3. Re-run validation
4. Only proceed when all checks pass
```

- [ ] **Step 2: Test the skill**

Run: Verify the skill file is correctly structured and referenced.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/cortex-phase-executor/SKILL.md
git commit -m "feat: add cortex-phase-executor skill for automated phase execution"
```

---

## Task 3: Create /project:next Command

**Files:**
- Create: `.claude/commands/project/next.md`

**Interfaces:**
- Consumes: cortex-repo-discovery, cortex-planning-ecosystem, cortex-phase-executor
- Produces: Auto-execution of next phase or version completion message

- [ ] **Step 1: Write the /project:next command**

```markdown
# /project:next — Continue Development

Auto-detect and execute the next phase. Chains phases together for continuous development.

## Instructions

### 1. Discovery

Invoke `cortex-repo-discovery`.

### 2. Find Current State

Read active version's progress.md.

Find the first phase with status "Not started".

### 3. If Phase Exists

Show: "Next: P0X — <name>. Executing..."

Auto-invoke `/project:cortex` with the phase.

### 4. If Version Complete

Show:
```
## Version Complete: vX.XX — <name>

All phases completed.
**Total Duration:** X days
**Capabilities Implemented:** N

Next version: v(Y).XX — <name>
Run /project:start v(Y).XX to continue.
```

### 5. If All Versions Complete

Show: "All versions complete. CORTEX is fully implemented."
```

- [ ] **Step 2: Test the command**

Run: Verify the command correctly finds the next phase.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/next.md
git commit -m "feat: add /project:next command for phase chaining"
```

---

## Task 4: Create /project:phase Command

**Files:**
- Create: `.claude/commands/project/phase.md`

**Interfaces:**
- Consumes: cortex-repo-discovery, cortex-planning-ecosystem
- Produces: Manual phase execution

- [ ] **Step 1: Write the /project:phase command**

```markdown
# /project:phase — Execute Specific Phase

Manually select and execute a specific phase from any version.

## Usage

```
/project:phase v1.02 P03
```

If no arguments: show available phases and let user select.

## Instructions

### 1. Discovery

Invoke `cortex-repo-discovery`.

### 2. Parse Arguments

If version and phase provided (e.g., `v1.02 P03`):
- Read `.agents/plans/versions/v1.02/P03.md`
- Execute via cortex-phase-executor

If no arguments:
- Read IMPLEMENTATION_STEPS.md
- Show all versions with phase status (from progress.md)
- Let user select

### 3. Execute

Auto-invoke `/project:cortex` with the selected version and phase.
```

- [ ] **Step 2: Test the command**

Run: Verify manual phase selection works.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/phase.md
git commit -m "feat: add /project:phase command for manual phase execution"
```

---

## Task 5: Enhance /project:cortex Command

**Files:**
- Modify: `.claude/commands/project/cortex.md`

**Interfaces:**
- Consumes: All cortex-* skills, shared-phases.md
- Produces: Full implementation cycle for a phase

- [ ] **Step 1: Read current cortex.md**

Read the existing file to understand current structure.

- [ ] **Step 2: Update version references**

Change all references from old V1-V6 to new v1.01-v1.14 format.

Update phase references to match new plan structure.

- [ ] **Step 3: Add phase-executor integration**

Add instruction to use cortex-phase-executor skill for task execution.

- [ ] **Step 4: Add progress tracking**

Add instruction to update progress.md after each phase.

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/project/cortex.md
git commit -m "enhance: update /project:cortex for v1.01-v1.14 plan structure"
```

---

## Task 6: Update shared-phases.md

**Files:**
- Modify: `.agents/plans/shared-phases.md`

**Interfaces:**
- Consumes: All cortex-* skills
- Produces: Updated shared phase definitions

- [ ] **Step 1: Add Phase Execution phase**

Add a new shared phase that delegates to cortex-phase-executor.

- [ ] **Step 2: Update all phase references**

Ensure all shared phases reference the correct skill names.

- [ ] **Step 3: Commit**

```bash
git add .agents/plans/shared-phases.md
git commit -m "enhance: update shared phases with phase executor integration"
```

---

## Task 7: Create cortex-progress-tracker Skill

**Files:**
- Create: `.claude/skills/cortex-progress-tracker/SKILL.md`

**Interfaces:**
- Consumes: progress.md files
- Produces: Updated progress.md, completion reports

- [ ] **Step 1: Write the skill**

```markdown
# cortex-progress-tracker

Track and update version/phase progress. Provides read/write access to progress.md files.

## When to Use

After completing a phase, task, or version. Before starting new work to check current state.

## Process

### 1. Read Current State

Read the version's progress.md file.

Parse: phases, statuses, completion times.

### 2. Update Status

After phase completion:
- Set phase status to "Completed"
- Record completion timestamp
- Update summary (completed count, remaining count)

### 3. Generate Report

Output:
```
## Progress: vX.XX — <name>

| Phase | Status | Completed |
|-------|--------|-----------|
| P01 | ✅ Completed | 2026-06-27 |
| P02 | ✅ Completed | 2026-06-27 |
| P03 | 🔄 In Progress | — |
| P04 | ⏳ Not started | — |

**Progress:** 2/4 phases (50%)
**Estimated Remaining:** 2-3 hours
```

### 4. Milestone Detection

When a version completes:
- Mark version as complete in progress.md
- Check if all dependencies for next version are met
- Report: "vX.XX complete. Ready for v(Y).XX."
```

- [ ] **Step 2: Test the skill**

Run: Verify progress tracking works with a test progress.md.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/cortex-progress-tracker/SKILL.md
git commit -m "feat: add cortex-progress-tracker skill for progress management"
```

---

## Task 8: Update CLAUDE.md References

**Files:**
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: New command/skill structure
- Produces: Updated execution contract

- [ ] **Step 1: Update command table**

Add /project:start, /project:next, /project:phase to the strategic commands table.

- [ ] **Step 2: Update workflow section**

Update the mandatory workflow to reference the new automated flow.

- [ ] **Step 3: Add quick start section**

Add a "Quick Start" section showing the automated development flow.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with enhanced development ecosystem"
```

---

## Execution Order

1. Task 1: /project:start command (entry point)
2. Task 2: cortex-phase-executor skill (core engine)
3. Task 3: /project:next command (phase chaining)
4. Task 4: /project:phase command (manual selection)
5. Task 5: Enhance /project:cortex (update existing)
6. Task 6: Update shared-phases.md (integration)
7. Task 7: cortex-progress-tracker skill (tracking)
8. Task 8: Update CLAUDE.md (documentation)

## Verification

After all tasks:
1. Run `/project:start` — should display current status
2. Run `/project:cortex` — should execute the next phase
3. Run `/project:next` — should chain to next phase
4. Run `/project:phase v1.02 P03` — should execute specific phase
5. All commands should update progress.md correctly
6. All commands should reference GUIDE.md and IMPLEMENTATION_STEPS.md

---

*Plan complete. Ready for execution.*
