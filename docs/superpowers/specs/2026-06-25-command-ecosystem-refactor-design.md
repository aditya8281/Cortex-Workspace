# Cortex Command Ecosystem Refactor — Design Spec

**Date:** 2026-06-25
**Status:** Draft
**Author:** Claude + Human (collaborative design)

---

## 1. Problem Statement

The Cortex repository has 7 standalone commands in `.claude/commands/project/`. They are independent, non-overlapping, and useful — but they don't compose. There is no master orchestrator. There is no way to run a complete development iteration by invoking a single command. Future development requires large prompts or manual orchestration.

Additionally, there is no mechanism for generating ecosystem-aware prompts. Users writing ad-hoc prompts often bypass existing workflows, skills, hooks, and governance — reinventing what the ecosystem already handles.

## 2. Goals

1. Create a master orchestrator command (`/cortex`) that autonomously executes one complete development iteration
2. Create a prompt generator command (`/prompt`) that produces ecosystem-aware development prompts
3. Add 4 new expert commands: `/audit`, `/verify`, `/release`, `/feature-gap`
4. Refine 7 existing commands for clarity and overlap elimination
5. Create a quick guide for command discoverability
6. Integrate all commands with existing governance, workflows, hooks, skills, and planning systems
7. Future development sessions should typically require only `/cortex`

## 3. Non-Goals

- Commands that programmatically invoke other commands (commands are markdown instructions, not functions)
- Changing the `.claude/commands/project/` file format or mechanism
- Creating a command dependency graph or import system
- Modifying the existing hook, skill, or workflow systems

## 4. Command Ecosystem Architecture

### 4.1 Three-Tier Design

```
Tier 1: Master Orchestrator
  /cortex          Autonomous development iteration

Tier 2: Prompt Generator
  /prompt          Ecosystem-aware prompt generation

Tier 3: Expert Commands (standalone, reusable)
  /audit           Codebase audit
  /review          Code quality review
  /verify          Verification suite
  /release         Release readiness
  /architecture    Architecture alignment
  /challenge       Adversarial review
  /health          Repository health
  /ideas           Innovation discovery
  /improve         Ecosystem self-improvement
  /reflect         Reflection framework
  /feature-gap     Roadmap vs codebase
```

### 4.2 How Tiers Relate

- `/cortex` is fully autonomous — invoke and walk away
- `/prompt` is collaborative — generates a prompt, user reviews, then uses it
- Expert commands are focused tools — invoked for specific tasks
- **No command calls another command.** `/cortex` implements equivalent workflows internally. `/prompt` references ecosystem components in generated prompts but doesn't invoke them.

### 4.3 File Structure

```
.claude/commands/
├── GUIDE.md                    # Quick reference guide
└── project/
    ├── cortex.md               # NEW: master orchestrator
    ├── prompt.md               # NEW: prompt generator
    ├── audit.md                # NEW: codebase audit
    ├── verify.md               # NEW: verification suite
    ├── release.md              # NEW: release readiness
    ├── feature-gap.md          # NEW: roadmap vs codebase
    ├── architecture.md         # EXISTING: refine
    ├── challenge.md            # EXISTING: refine
    ├── health.md               # EXISTING: refine
    ├── ideas.md                # EXISTING: refine
    ├── improve.md              # EXISTING: refine
    ├── reflect.md              # EXISTING: refine
    └── review.md               # EXISTING: refine
```

---

## 5. Master Orchestrator: `/cortex`

### 5.1 Pipeline

```
Phase 0: CONTEXT     Read everything. Determine position.
Phase 1: PLAN        Decide iteration scope. Think critically.
Phase 2: BRANCH      Create isolation.
Phase 3: BUILD       Implement the planned work.
Phase 4: VALIDATE    Tests, lint, build.
Phase 5: REVIEW      Quality + adversarial.
Phase 6: REFLECT     Improve, update tracking.
Phase 7: CLEANUP     Remove unnecessary files, artifacts.
Phase 8: COMMIT      Meaningful commits, ready for merge.
Exit gate → loop or complete.
```

### 5.2 Phase Details

#### Phase 0: CONTEXT

Read all state to understand where the repo is:

- `.agents/plans/guide.md` — constitution, architecture principles
- `.agents/plans/implementation_steps.md` — execution plan
- `.agents/plans/versions/vX/Phase-N.md` — active phase plan
- `.agents/plans/versions/vX/progress.md` — progress tracker
- `ACTIVE_VERSION.md` — current version
- Git state: branch, recent commits, uncommitted work
- `make check` — current test/lint status

#### Phase 1: PLAN (Critical Thinking)

**When a plan exists:**
- Read it thoroughly
- Challenge every step: Is this still the best approach? Are assumptions valid? Has anything changed?
- Adapt: If a better approach emerges, use it. Document the deviation and why.
- Question scope: Too broad? Too narrow? Should it be split?
- Verify file targets: Do referenced files still exist? Have they changed?
- Assess dependencies: Does the plan account for all integration points?

**When no plan exists:**
- Determine what work is needed from context
- Create a brief plan (don't skip planning)
- Apply the same critical thinking

**The plan is guidance, not gospel. The agent's judgment supersedes the plan when the agent can articulate why.**

Select applicable skills from `.claude/skills/`. Determine if brainstorming skill is needed for complex design decisions.

#### Phase 2: BRANCH

- Create `feat/<topic>` from `main`
- Verify clean starting state

#### Phase 3: BUILD

- Implement the planned work following TDD when applicable
- Commit after each logical unit
- Run `make lint` + `make format` after each commit
- Run relevant tests after each commit
- Use subagents for multi-file work when beneficial
- Leverage MCP servers where appropriate (context7 for docs, etc.)

#### Phase 4: VALIDATE

- `make test` (backend)
- `cd frontend && npm test` (frontend)
- `make lint` + `make format`
- `make hooks-onchange`
- If anything fails: loop back to Phase 3

#### Phase 5: REVIEW

- Equivalent of `/review` (code quality)
- If architectural decision: equivalent of `/challenge`
- Address all P0/P1 findings
- If critical issues found: loop back to Phase 3

#### Phase 6: REFLECT

- Equivalent of `/reflect`
- Update progress.md
- Update relevant docs if architecture changed
- Check if new ADR needed

#### Phase 7: CLEANUP

After reflection, before final commit:
- Identify files created during this iteration that are unnecessary (scratch files, temp outputs, abandoned approaches)
- Delete them
- Check for any new TODO/FIXME introduced that should be resolved or documented
- Verify no stale references to removed files exist in docs or imports
- Run `git status` to confirm only intended files are staged

#### Phase 8: COMMIT

- Meaningful commit messages following conventions
- Verify `make hooks-merge` passes
- Leave repo ready for merge
- Report what was done

### 5.3 Exit Gate

- All tests pass
- Lint clean
- No P0/P1 findings
- Progress updated
- If exit criteria not met: loop back to Phase 3 (max 3 iterations)

### 5.4 Escalation to Human

The command pauses and asks the user when:
- Decision would change architecture or vision
- Multiple valid paths with no clear winner
- Max loop iterations exceeded
- Unexpected blocker that can't be resolved autonomously
- Scope ambiguity that the repo cannot resolve

---

## 6. Prompt Generator: `/prompt`

### 6.1 Pipeline

```
Step 1: UNDERSTAND    Read repo state, roadmap, architecture, ecosystem.
Step 2: CLASSIFY      Determine prompt type from user's stated goal.
Step 3: GENERATE      Write prompt that routes through existing systems.
Step 4: REVIEW        Self-audit the generated prompt.
Step 5: REFINE        Improve until it meets quality bar.
Step 6: PRESENT       Show final prompt to user.
```

### 6.2 Step 1: UNDERSTAND

Before generating anything, read:
- Current git state (branch, recent commits, uncommitted work)
- Active version and phase (progress.md, ACTIVE_VERSION.md)
- Architecture (docs/ARCHITECTURE.md)
- Constitution (.agents/plans/guide.md)
- Workflows (docs/WORKFLOWS.md)
- Governance (docs/GOVERNANCE.md)
- Available skills (.claude/skills/)
- Available commands (.claude/commands/project/)
- Available hooks (.claude/hooks/)
- Available MCP servers (from settings)

### 6.3 Step 2: CLASSIFY

| Category | What It Generates | Ecosystem Leverage |
|----------|------------------|-------------------|
| **Planning** | Brainstorming/design prompt | Routes through brainstorming skill, references guide.md |
| **Architecture** | Architectural decision prompt | Routes through /architecture or /challenge, references ADRs |
| **Feature** | Implementation prompt | Routes through /cortex workflow, references phase plan |
| **Bug Fix** | Diagnosis and fix prompt | Routes through TDD pattern, references test infrastructure |
| **Audit** | Repository audit prompt | Routes through /audit, references hooks and automation |
| **Documentation** | Doc writing prompt | References docs/ structure, governance rules |
| **Refactor** | Restructuring prompt | Routes through /review + /challenge, references architecture |
| **Performance** | Optimization prompt | References benchmarks, profiling approach |
| **Frontend** | UI/UX prompt | References DESIGN.md, frontend architecture in CLAUDE.md |
| **Backend** | API/service prompt | References backend architecture, service patterns, auth model |
| **DevOps** | Infrastructure prompt | References Makefile, docker-compose, CI pipeline |
| **Security** | Security review prompt | Routes through AGENTS.md patterns, references docs/SECURITY.md |
| **Testing** | Test creation prompt | References tests/ structure, conftest.py patterns |
| **Release** | Release prep prompt | Routes through /release, references version system |
| **Ecosystem** | Ecosystem improvement prompt | Routes through /improve, references governance |
| **Generation** | Command/hook/skill creation prompt | References existing patterns, governance rules |

### 6.4 Step 3: GENERATE

Generated prompts follow this structure:

```
# [Objective]

## Context
[What this builds on — references real files, real state]

## Constraints
[Architecture rules, governance — from guide.md and CLAUDE.md]

## Approach
[How to do it — references real skills, workflows, hooks]

## Validation
[How to verify — references real make targets, test commands]

## References
[Links to relevant docs, ADRs, existing patterns]
```

**Key rules:**
- Reference real file paths that exist in the repo
- Reference real skills that exist in `.claude/skills/`
- Reference real workflows from `docs/WORKFLOWS.md`
- Reference real governance from `docs/GOVERNANCE.md`
- Don't repeat rules already enforced by hooks
- Don't duplicate architecture constraints — reference `guide.md`
- Be concise for simple tasks, detailed for complex ones
- Scale detail to actual complexity

### 6.5 Step 4: REVIEW (Self-Audit)

Before presenting, audit the generated prompt:

1. **Clarity:** Would an agent know exactly what to do?
2. **Scoping:** Is the scope defined? Can it be done in one iteration?
3. **Ecosystem leverage:** Does it use existing systems or reinvent them?
4. **Redundancy:** Does it repeat rules already handled by the ecosystem?
5. **Completeness:** Are all integration points mentioned?
6. **Simplicity:** Can it be shorter without losing effectiveness?

### 6.6 Step 5: REFINE

Fix any issues found in review. Repeat until all 6 checks pass.

### 6.7 Step 6: PRESENT

Show the final prompt in a code block. Offer to:
- Edit based on feedback
- Save to a file
- Copy for immediate use

---

## 7. New Expert Commands

### 7.1 `/audit` — Codebase Audit

**Purpose:** Deep code-level scan for runtime errors, dead code, integration issues, broken imports, placeholders, and technical debt.

**Scope (vs `/health`):** `/health` = broad ecosystem (skills, docs, governance, trends). `/audit` = deep code (imports, integration chains, mock consistency, placeholder detection).

**Instructions:**
1. Read active phase plan for scope
2. Run `make check` for baseline
3. Scan for runtime errors (imports, singletons, response_model, ownership checks)
4. Scan for dead code (apply UNIQUE CAPABILITIES test — not imported ≠ dead)
5. Scan for integration issues (service chains, mock patches, model imports)
6. Scan for placeholders (TODO, FIXME, NotImplementedError, mock implementations)
7. Scan for consistency (CLAUDE.md vs code, docs references, migration chain)

**Output:** Structured table with severity, file:line, issue, fix for each finding.

### 7.2 `/verify` — Verification Suite

**Purpose:** Run automated checks and report pass/fail. Fast, focused, no analysis.

**Scope (vs `/review`):** `/review` = should we ship (quality, patterns). `/verify` = can we ship (tests, lint, build pass).

**Checks:**
1. Backend tests (`make test`)
2. Frontend tests (`cd frontend && npm test`)
3. Lint (`make lint`)
4. Format (`make format --check`)
5. Build (`cd frontend && npm run build`)
6. Hooks (`python3 .claude/hooks/run_hooks.py`)
7. Migrations (`make migrate`)

**Output:** Pass/fail table per check. Block merge on any FAIL.

### 7.3 `/release` — Release Readiness

**Purpose:** Determine if the current state is ready for release of the active version/phase.

**Scope (vs `/verify`):** `/verify` = do tests pass. `/release` = is this version/phase complete and releasable.

**Checks:**
1. Read version context (ACTIVE_VERSION.md, progress.md, phase plan)
2. Run all `/verify` checks
3. Check phase completeness against exit criteria
4. Check documentation (API.md, DATABASE.md, ARCHITECTURE.md, ADRs)
5. Check governance (hooks, progress.md, unresolved findings)
6. Check git state (clean tree, meaningful commits, no conflicts)
7. Check version boundaries (scope creep detection)

**Output:** Readiness verdict (READY / NOT READY) with blockers list.

### 7.4 `/feature-gap` — Roadmap vs Codebase Gap Analysis

**Purpose:** Cross-reference roadmap/phase plans against actual codebase. Find what's missing.

**Scope (vs `/audit`):** `/audit` = issues in existing code. `/feature-gap` = planned work that hasn't been implemented.

**Process:**
1. Read roadmap and active phase plan
2. Scan backend/app/services/, api/v1/, models/, frontend/src/
3. Cross-reference planned components vs implemented components
4. Classify: Complete / Partial / Stubbed / Missing
5. Estimate effort per gap (S/M/L)

**Output:** Gap table with component, status, tests, effort. Recommended priority order.

---

## 8. Refinements to Existing Commands

| Command | Change | Reason |
|---------|--------|--------|
| `/architecture` | Add ACTIVE_VERSION.md check, reference guide.md principles | Align with current version context |
| `/challenge` | Add version boundary check (scope-appropriate for current version?) | Prevent scope creep |
| `/health` | Clarify: broad ecosystem only, code-level is `/audit` | Eliminate overlap with `/audit` |
| `/ideas` | Cross-reference with `/feature-gap` results if available | Better prioritization |
| `/improve` | Check if new commands/hooks/skills should be created from patterns | Close self-improvement loop |
| `/reflect` | Check if findings should become new skills/hooks/commands | Connect reflection to growth |
| `/review` | Clarify: code quality only, not verification (that's `/verify`) | Eliminate overlap with `/verify` |

---

## 9. Quick Guide

Create `.claude/commands/GUIDE.md` with:
- How to use commands (`/project:<name>`)
- All 13 commands in a table with purpose and when-to-use
- Typical workflows (quick session, big decision, weekly maintenance, before release, need a prompt)
- Priority order (cortex > prompt > everything else)

---

## 10. Integration Map

| System | How Commands Integrate |
|--------|----------------------|
| **CLAUDE.md** | `/cortex` references as execution contract. All commands assume rules active. `/prompt` references constraints, not duplicates. |
| **AGENTS.md** | `/audit` checks security patterns. `/challenge` verifies principles. `/prompt` routes security prompts through AGENTS.md. |
| **Workflows** | `/cortex` implements 8-stage workflow internally. `/prompt` references stages. |
| **Hooks** | `/cortex` runs at VALIDATE and COMMIT. `/verify` reports results. `/release` gates on pass. |
| **Skills** | `/cortex` selects during PLAN. `/prompt` references in generated prompts. `/improve` reviews health. |
| **Governance** | `/cortex` follows throughout. `/challenge` checks alignment. `/release` gates on compliance. |
| **Planning** | `/cortex` reads phase plans and progress. `/feature-gap` cross-references. `/prompt` references active plans. |
| **MCP Servers** | `/cortex` uses context7 during BUILD. `/prompt` mentions relevant servers. |
| **Automation** | `/health` runs health checks. `/audit` runs bug discovery. `/cortex` runs during VALIDATE. |

---

## 11. Design Principles

1. **No command-to-command calls.** Commands are instructions for Claude, not functions. The master command implements equivalent workflows internally.
2. **Single source of truth.** Commands reference existing docs, not duplicate them.
3. **Composable, not coupled.** Each expert command works standalone. `/cortex` is a convenience that orchestrates the equivalent workflows.
4. **Critical thinking over blind execution.** Plans are guidance. The agent's judgment supersedes when it can articulate why.
5. **Cleanup is part of the cycle.** Every iteration ends with removing unnecessary artifacts.
6. **Prompts should be ecosystem-aware.** `/prompt` ensures work routes through existing systems, not around them.
7. **Clear separation of concerns.** `/verify` ≠ `/review`. `/audit` ≠ `/health`. Each has a distinct scope.

---

## 12. Success Criteria

1. `/cortex` can execute one complete development iteration autonomously
2. `/prompt` generates prompts that reference real ecosystem components
3. All 13 commands are discoverable via the quick guide
4. No command duplicates another's responsibility
5. All commands follow consistent structure (Purpose → Instructions → Output)
6. Integration with governance, workflows, hooks, skills, and planning is explicit
7. A typical development session starts with `/cortex` and requires minimal follow-up
