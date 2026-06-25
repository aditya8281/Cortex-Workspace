# /project:develop — Development Iteration Orchestrator

**NOT** an implementation command. An **orchestrator**. It determines next work, generates a brief if needed, delegates execution, and runs reflection — using the existing Cortex ecosystem.

## When to Run

Start of a development session, or after merging a completed iteration. Do **not** run during active implementation — `/project:cortex` handles that.

## Philosophy

`/project:develop` owns the loop, not the work.

| Command | Role |
|---------|------|
| `/project:develop` | Decide what to do next → brief → orchestrate → reflect → report |
| `/project:prompt` | Generate ecosystem-aware implementation prompts |
| `/project:cortex` | Execute a full implementation iteration (Phases 0-8) |
| `/project:verify` | Run automated validation checks |
| `/project:review` | Code quality analysis |
| `/project:reflect` | Post-completion reflection framework |

This command invokes those workflows conceptually. It does **not** duplicate their instructions.

## Instructions

### Step 1: Discover Repository State

Run:

```bash
# Current state
git status
git branch --show-current
git log --oneline -5

# What's the active version and phase?
cat .agents/plans/ACTIVE_VERSION.md 2>/dev/null || echo "No ACTIVE_VERSION.md"
grep -r "in_progress\|active" .agents/plans/versions/*/progress.md 2>/dev/null || true

# Any uncommitted work or branches?
git stash list
```

Read:

- `.agents/plans/implementation_steps.md` — execution order
- Active plan file: `.agents/plans/versions/v{ACTIVE}/Phase-{N}.md` — current phase
- Active progress: `.agents/plans/versions/v{ACTIVE}/progress.md` — what's done/not done
- `docs/ROADMAP.md` (if present) — broader roadmap

**Outcome:** A clear picture of where the project is and what's incomplete.

---

### Step 2: Determine Highest-Priority Work

From the active phase plan and progress tracking, find the **highest-priority unfinished item**.

Priority ordering:

1. **Critical blockers** — items blocking all other work (P0)
2. **In-progress items** — partially done, resume before starting new
3. **Phase priorities** — items ordered by the phase plan
4. **Dependency chain** — items that must precede others
5. **Risk reduction** — unknowns that should be validated early

If only one incomplete item exists → that's the task.

If multiple → pick by:
- Dependency order first
- Risk reduction second
- Plan ordering third

If all phase items are complete → check if the phase exit criteria are met. If yes, the work is advancing to the next phase — note this.

**Outcome:** A single next task identified, with rationale.

---

### Step 3: Generate Execution Brief (If Ambiguous)

If the next task is **well-understood** (clear scope, bounded, familiar pattern) → skip this step. The task description from Step 2 is sufficient.

If the next task is **ambiguous** (new subsystem, cross-cutting, unfamiliar domain, >2 files likely affected) → generate an execution brief.

The brief is **not** a full `/project:prompt` output. It is a lightweight scoping document:

```markdown
## Execution Brief

### Task
[One-line description]

### Scope
- Files likely affected:
- Modules involved:
- Known unknowns:

### Approach
[Brief implementation strategy — 3-5 sentences]

### Dependencies
[What must exist before this work can begin]

### Risks
[What could go wrong]
```

**How to generate:** Read relevant source files, ADRs, and the architecture guide. Do not invoke `/project:prompt` as a sub-command — the brief is lighter. Use `/project:prompt` logic (discover, classify, clarify) as the mental model, not the implementation.

Save the brief to a temporary note if needed; do not persist it beyond the session.

**Outcome:** Either the task is well-understood (no brief needed) or a lightweight brief exists.

---

### Step 4: Execute via Cortex Workflow

This step conceptually invokes the `/project:cortex` workflow.

Pass the task (and optional brief) as the implementation objective. The cortex workflow handles:

- Phase 0: Repository Intelligence (discovers relevant context)
- Phase 1: Strategic Planning (plans the implementation)
- Phase 2: Branch (creates working branch)
- Phase 3: Implementation Loop (TDD, iterate)
- Phase 4: System Validation (test, lint, format)
- Phase 5: Engineering Review (quality check)
- Phase 6: Reflection (run reflection framework)
- Phase 7: Repository Cleanup (clean up)
- Phase 8: Version Integrity (merge readiness)
- Exit Gate (verify all criteria met)

**Do not** copy those 8 phases into this command. They live in `/project:cortex` — reference it.

**Exception:** If the task is trivial (single file, mechanical change, no branching needed), skip the full cortex workflow and implement directly. Use judgment — when in doubt, run the full workflow.

**Outcome:** Implementation complete, tests passing, lint clean, branch ready.

---

### Step 5: Track Deviations

During execution, one of these happens:

- **No deviation** — the plan was followed as designed → no action needed
- **Justified deviation** — a better approach was discovered, or a constraint invalidated the plan → update planning artifacts:
  - Update progress.md if task status changed
  - Update phase plan if scope changed
  - Create ADR if architectural decision was made
  - Update `.agents/plans/guide.md` if principle-level change
- **Unjustified deviation** — the implementation drifted without justification → flag in the completion report, recommend remediation

**Outcome:** Planning artifacts reflect reality. No stale documentation.

---

### Step 6: Run Reflection

Conceptually invoke the `/project:reflect` framework.

The reflection covers:

1. **Identify work completed** — files changed, features implemented, bugs fixed
2. **Quality** — code cleanliness, error handling, edge cases
3. **Redundancy** — duplication, consolidation opportunities
4. **Automation** — manual steps, hook/skill opportunities
5. **Documentation gaps** — outdated or missing docs
6. **Test gaps** — missing coverage, edge case tests
7. **Technical debt** — shortcuts, TODOs, postponed refactors
8. **Ecosystem impact** — commands, hooks, workflows, skills to update
9. **Architecture review** — coupling, cohesion, layer separation

**Do not** copy the full reflection framework here. It lives in `/project:reflect` — reference it.

If the reflection identifies action-items:

1. Apply them if they belong in this iteration (quick wins)
2. Defer them to a follow-up iteration if they require separate work
3. Document deferred items in progress.md or an audit report

Save reflection to `docs/audits/YYYY-MM-DD-reflect-{N}.md` if any action-item exists.

**Outcome:** Reflection complete. Action-items resolved or deferred. Report saved if needed.

---

### Step 7: Produce Completion Report

```text
## Development Iteration: YYYY-MM-DD

### Task
[What was worked on]

### Rationale
[Why this was the highest-priority work]

### Outcome
[What was completed, what wasn't]

### Files Changed
[M / C / D — summary or count]

### Validation
- Tests: PASS / FAIL (N)
- Lint: PASS / FAIL
- Format: PASS / FAIL

### Reflection
- Action-items applied: N
- Action-items deferred: N (list)
- Report saved: path/to/reflect-N.md

### Ecosystem Updates
[Commands, hooks, workflows, skills, docs, config updated]

### Technical Debt
[Items remaining, known limitations]

### Next Likely Task
[What Step 2 would return if run again]

### State
- Branch: [name]
- Ready to merge: YES / NO
- Merge strategy: [ff-only / --no-ff]
```

---

## Phases Overview

The full development lifecycle is documented across these commands:

| Phase | Command | When |
|-------|---------|------|
| Triage & Classification | `/project:develop` Step 2 | Session start, ambiguous tasks |
| Prompt Generation | `/project:prompt` | Complex tasks needing structured spec |
| Full Implementation | `/project:cortex` | Every significant implementation |
| Verification | `/project:verify` | Pre-merge automated checks |
| Code Review | `/project:review` | Pre-push quality analysis |
| Architecture Check | `/project:architecture` | Before architectural changes |
| Adversarial Review | `/project:challenge` | Before major decisions |
| Reflection | `/project:reflect` | Before completion sign-off |
| Release Readiness | `/project:release` | Before release |
| Health Check | `/project:health` | Weekly |
| Ecosystem Improvement | `/project:improve` | Weekly or after significant work |
| Feature Gap Analysis | `/project:feature-gap` | During planning |
| Ideas | `/project:ideas` | Weekly |

## Commit Guideline

RULE (SHOULD ALWAYS FOLLOW): always make git msg of one line in standard manner, and never add any co authored by text never.
