# /project:cortex — Implementation Workflow

Executes a complete implementation iteration. For concrete, well-defined tasks with clear scope.

**When to run:** You have a concrete task. For ambiguous requests, use `/project:update` or `/project:develop` first.

## Absolute Rules

### Skill-First — ALWAYS

Before ANY action in this workflow, check for applicable skills. No exceptions.

### Frontend = Design Excellence

If ANY work touches `frontend/`:
- **Before implementation:** Invoke `superpowers:brainstorming` for design decisions
- **Before coding:** Invoke `superpowers:writing-plans` for structured implementation plan
- **After implementation:** UI Review hook auto-validates design tokens, glassmorphism, accessibility
- **Before merge:** Playwright hook validates build + visual regression
- **Always:** Use context7 for latest React/Next.js/Tailwind docs

### Brainstorm Before Planning

When a phase plan involves significant design decisions (new UI, new API surface, architectural change):
1. Invoke `superpowers:brainstorming` to explore approaches
2. Present 2-3 options with trade-offs
3. Get user approval on design
4. THEN invoke `superpowers:writing-plans` to create implementation plan
5. Execute plan via TDD

### Create Skills for Repeated Patterns

If you execute the same workflow 2+ times:
1. Complete current execution
2. Invoke `superpowers:writing-skills` to create a persistent skill
3. Save to `.claude/skills/<skill-name>/SKILL.md`
4. Log: "Created skill: <name> for <pattern>"

---

## Phases

### P0: Repository Intelligence + Ecosystem Integration

Invoke `cortex-repo-discovery` then `cortex-repository-intelligence` then `cortex-ecosystem-integration`.

Then read `.agents/plans/GUIDE.md`, `.agents/plans/IMPLEMENTATION_STEPS.md`, active phase plan, and active progress. Identify existing related implementations — prefer extending over creating new.

**Outcome:** Repo state, version, phase, related implementations understood. All ecosystem capabilities mapped.

---

### P1: Strategic Planning

Determine approach. If a plan exists: read, challenge, verify, adapt. If not: create one. Determine objectives, affected modules, dependencies, risks, validation strategy. Select applicable skills. Only ask the user when multiple valid directions with no better choice.

**If the phase involves significant design decisions:**
Invoke `superpowers:brainstorming` to explore approaches before planning.

**Outcome:** Clear plan.

---

### P2: Branch

```bash
git checkout -b <type>/<topic>
```

Verify clean tree, correct naming, repo ready.

---

### P3: Implementation Loop

Invoke `cortex-phase-executor` for the active phase plan (e.g., `.agents/plans/versions/vX.XX/P0N.md`).

The skill reads the phase file, parses all tasks, and executes each sequentially via TDD cycle:
1. Write failing test → verify fail
2. Implement minimal code → verify pass
3. Commit with descriptive message
4. Repeat for next task

After all tasks: run validation (`make test`, `make lint`, `make format`).

**Outcome:** All phase tasks completed, tests passing, clean commits.

---

### P4: System Validation + Auto-Resolve

Invoke `cortex-system-validation`. For any failure:
- Read the error output
- Identify root cause
- Fix the code (not the test — unless test is wrong)
- Re-run to confirm pass
- Commit fix: `fix: auto-resolve validation failure in <component>`
- Max 3 fix attempts per issue, then escalate

Never stop for failures — auto-fix and continue.

---

### P5: Engineering Review + Auto-Resolve

Invoke `cortex-engineering-review`, `cortex-architecture-drift`, `cortex-adversarial-challenge`.

For any P0/P1 findings: auto-fix immediately (fix the code, not the finding). If fix requires significant refactor, return to P3 for that specific item. Advisory findings (P2/P3) are logged but don't block.

**Outcome:** Quality confirmed, architecture aligned, risks identified.

---

### P6: Progress Update & Reflection

Invoke `cortex-progress-tracker` to update progress.md with completion status and timestamp.

Invoke `cortex-post-reflection` for systematic analysis. Apply action-items. Update architecture docs, ADRs, plans as needed.

**If repeated patterns found:** Invoke `superpowers:writing-skills` to create new skill.

---

### P7: Repository Cleanup

Invoke `cortex-repo-cleanup`.

---

### P8: Version Integration

Invoke `cortex-version-integration`.

---

## Exit Gate

All must be true:
- [ ] Objectives completed
- [ ] Validation passed
- [ ] Engineering review completed
- [ ] Reflection completed
- [ ] Documentation updated where required
- [ ] Configuration updated where required
- [ ] Progress tracking updated
- [ ] Repository cleanup completed
- [ ] Repository ready for merge

Max 3 full iteration loops before escalating.

---

## Escalation

Pause for user only when: architecture change, product/roadmap change, conflicting sources of truth, ambiguous requirements after analysis, multiple equally-valid solutions, unsafe migration, max loops exceeded, unresolvable blocker.

---

## Output

```text
## Cortex Iteration: [date]

### Repository Intelligence
### Objectives
### Work Completed
### Files Changed
### Repository Impact
### Validation [PASS / FAIL]
### Engineering Review
### Reflection
### Ecosystem Updates
### Skills Created
### Technical Debt
### Commits

### Final Status
- Tests: PASS / FAIL
- Lint: PASS / FAIL
- Hooks: PASS / FAIL
- Repository Ready: YES / NO
```

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:cortex",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
