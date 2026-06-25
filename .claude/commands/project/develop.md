# /project:develop — Development Iteration Orchestrator

**NOT** an implementation command. An **orchestrator**. Decides next work, generates brief if needed, delegates to `/project:cortex`, runs reflection, produces report.

## When to Run

Start of development session, or after merging a completed iteration. Not during active implementation — use `/project:cortex` for that.

## Philosophy

`/project:develop` owns the loop, not the work.

## Instructions

### Step 1: Discover Repository State

Invoke `cortex-repo-discovery` then `cortex-repository-intelligence`.

Also read active phase plan and progress tracking.

**Outcome:** Clear picture of where project is and what's incomplete.

---

### Step 2: Determine Highest-Priority Work

From active plan and progress, find the **highest-priority unfinished item**.

Priority: critical blockers → in-progress items → phase plan order → dependency chain → risk reduction.

If all phase items complete → check exit criteria. If met, note work is advancing to next phase.

**Outcome:** Single next task identified with rationale.

---

### Step 3: Generate Execution Brief (If Ambiguous)

If task is well-understood → skip.

If ambiguous (new subsystem, cross-cutting, >2 files likely affected) → generate lightweight brief:

```markdown
### Task
[One-line]
### Scope
- Files affected:
- Modules:
- Unknowns:
### Approach
[3-5 sentences]
### Dependencies
### Risks
```

Read relevant source files, ADRs, architecture guide. Do not invoke `/project:prompt` — brief is lighter.

**Outcome:** Either task is clear or lightweight brief exists.

---

### Step 4: Execute via Cortex Workflow

Conceptually invoke `/project:cortex` with task (and optional brief). It handles P0-P8.

**Exception:** Trivial tasks (single file, mechanical) → implement directly.

**Outcome:** Implementation complete, tests passing, lint clean.

---

### Step 5: Track Deviations

- **No deviation** → no action
- **Justified deviation** → update progress.md, phase plan, ADRs, guide.md as needed
- **Unjustified drift** → flag in completion report, recommend remediation

**Outcome:** Planning artifacts reflect reality.

---

### Step 6: Run Reflection

Invoke `cortex-post-reflection`. Save to `docs/audits/YYYY-MM-DD-reflect-{N}.md` if action-items exist.

---

### Step 7: Produce Completion Report

```text
## Development Iteration: date

### Task
### Rationale
### Outcome
### Files Changed
### Validation (Tests/Lint/Format)
### Reflection (Applied/Deferred)
### Ecosystem Updates
### Technical Debt
### Next Likely Task
### State (Branch, Ready to merge, Merge strategy)
```
