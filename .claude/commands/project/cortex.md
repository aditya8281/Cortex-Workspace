# /project:cortex — Implementation Workflow

Executes a complete implementation iteration. For concrete, well-defined tasks with clear scope.

**When to run:** You have a concrete task. For ambiguous requests, use `/project:update` or `/project:develop` first.

## Phases

### P0: Repository Intelligence

Invoke `cortex-repo-discovery` then `cortex-repository-intelligence`.

Then read `.agents/plans/GUIDE.md`, `.agents/plans/IMPLEMENTATION_STEPS.md`, active phase plan, and active progress. Identify existing related implementations — prefer extending over creating new.

**Outcome:** Repo state, version, phase, related implementations understood.

---

### P1: Strategic Planning

Determine approach. If a plan exists: read, challenge, verify, adapt. If not: create one. Determine objectives, affected modules, dependencies, risks, validation strategy. Select applicable skills. Only ask the user when multiple valid directions with no better choice.

**Outcome:** Clear plan.

---

### P2: Branch

```bash
git checkout -b <type>/<topic>
```

Verify clean tree, correct naming, repo ready.

---

### P3: Implementation Loop

For each logical unit: plan smallest increment → implement → TDD where practical → self-review → lint/format → fix → commit. Extend existing code, avoid duplication, maintain consistency. Repeat until objectives complete.

**Outcome:** Working implementation, tests passing, clean commits.

---

### P4: System Validation

Invoke `cortex-system-validation`. Fix any failure before proceeding.

---

### P5: Engineering Review

Invoke `cortex-engineering-review`, `cortex-architecture-drift`, `cortex-adversarial-challenge`. Resolve P0/P1 before continuing. If significant issues, return to P3.

**Outcome:** Quality confirmed, architecture aligned, risks identified.

---

### P6: Post-Completion Reflection

Invoke `cortex-post-reflection`. Apply action-items. Update progress tracking, architecture docs, ADRs, plans as needed.

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
### Technical Debt
### Commits

### Final Status
- Tests: PASS / FAIL
- Lint: PASS / FAIL
- Hooks: PASS / FAIL
- Repository Ready: YES / NO
```
