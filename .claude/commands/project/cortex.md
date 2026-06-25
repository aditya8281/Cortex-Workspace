# /project:cortex — Implementation Workflow

Executes a complete implementation iteration. This is the **how** — detailed implementation guidance that the orchestrator `/project:develop` conceptually invokes.

**When to run directly:** You have a concrete, well-defined task with clear scope. For ambiguous or high-level requests, use `/project:update` or `/project:develop` instead.

**Relationship to other commands:** This command does not duplicate specialist tools. It references them.

## Phases

### Phase 0: Repository Intelligence

Run discovery steps from `.agents/plans/shared-phases.md#repository-intelligence`.

Then read:

- `.agents/plans/guide.md` — architecture principles
- `.agents/plans/implementation_steps.md` — execution order
- Active phase plan: `.agents/plans/versions/v{ACTIVE}/Phase-{N}.md`
- Active progress: `.agents/plans/versions/v{ACTIVE}/progress.md`
- `docs/ROADMAP.md` — broader roadmap

Also identify existing implementations related to the task. Prefer extending existing code.

**Outcome:** Repository state, active version, phase, and related implementations understood.

---

### Phase 1: Strategic Planning

Determine the approach.

When an implementation plan exists:

- Read it completely.
- Challenge assumptions — verify file locations, dependencies, integration points.
- Determine whether the plan is still optimal.
- Adapt when a better solution exists.
- Document significant deviations.

When no implementation plan exists: create one.

Determine:

- Objectives, deliverables
- Affected modules, APIs, commands, hooks, workflows, skills, docs, config, tests
- Dependencies, risks, validation strategy, rollback strategy, completion criteria

Select applicable skills from `.agents/skills/`.

If brainstorming or architecture exploration would materially improve the solution, use appropriate skills before implementation.

Only ask the user when multiple valid directions exist with no objectively better choice.

**Outcome:** Clear plan for what to implement and how.

---

### Phase 2: Branch

Create an isolated working branch:

```bash
git checkout -b <type>/<topic>  # e.g., feat/streaming-memory, fix/auth-bug
```

Verify:

- Working tree is clean
- Branch naming follows conventions
- Repository is ready for implementation

---

### Phase 3: Implementation Loop

Implement using small, verifiable iterations.

For each logical unit of work:

1. Plan the smallest complete increment.
2. Implement.
3. Follow TDD where practical.
4. Perform a quick self-review.
5. Run relevant linting and tests (`make lint` + `make format`).
6. Fix issues immediately.
7. Commit after each logical unit.

During implementation:

- Prefer extending existing implementations.
- Avoid duplicated logic.
- Maintain architecture consistency.
- Keep commits logical and atomic.
- Update documentation when behavior changes.
- Update configuration when required.
- Use subagents for parallel independent work.
- If a substantially better implementation is discovered, prefer it and explain the deviation.

Repeat until implementation objectives are complete.

**Outcome:** Working implementation, tests passing, clean commits.

---

### Phase 4: System Validation

Run `.agents/plans/shared-phases.md#system-validation`.

Fix any failures before proceeding.

---

### Phase 5: Engineering Review

Run `.agents/plans/shared-phases.md#engineering-quality-review`.

Run `.agents/plans/shared-phases.md#architecture-drift-detection`.

Run `.agents/plans/shared-phases.md#adversarial-challenge`.

Resolve every P0 and P1 issue before continuing.

If significant issues are found, return to Phase 3.

**Outcome:** Quality confirmed, architecture aligned, risks identified.

---

### Phase 6: Post-Completion Reflection

Run `.agents/plans/shared-phases.md#post-completion-reflection`.

Apply any action-items that belong in this iteration. Only defer when justified.

Update:

- Progress tracking
- Architecture documentation
- ADRs
- Implementation plans

when required.

---

### Phase 7: Repository Cleanup

Run `.agents/plans/shared-phases.md#repository-cleanup`.

---

### Phase 8: Version Integration

Run `.agents/plans/shared-phases.md#version-integration-check`.

---

## Exit Gate

The iteration is complete only when all of the following are true:

- [ ] Objectives completed
- [ ] Validation passed
- [ ] Engineering review completed
- [ ] Reflection completed
- [ ] Documentation updated where required
- [ ] Configuration updated where required
- [ ] Progress tracking updated
- [ ] Repository cleanup completed
- [ ] Repository ready for merge

If any requirement is not satisfied, return to the Implementation Loop.

Maximum three full iteration loops before escalating.

---

## Escalation Policy

Pause and ask the user only when:

- Architecture would change
- Product direction would change
- Roadmap direction would change
- Repository contains conflicting sources of truth
- Requirements remain ambiguous after repository analysis
- Multiple equally valid architectural solutions exist
- Implementation would require unsafe migration
- Maximum autonomous iterations have been exceeded
- A blocker cannot be resolved using repository context

Otherwise continue autonomously.

---

## Output

```text
## Cortex Iteration: [date]

### Repository Intelligence
[Current repository state]

### Objectives
[Iteration objectives]

### Work Completed
[Summary]

### Files Changed
[Modified / Created / Deleted]

### Repository Impact
- Modules
- APIs
- Commands
- Hooks
- Workflows
- Skills
- Documentation
- Configuration
- Tests

### Validation
[PASS / FAIL]

### Engineering Review
[Summary]

### Reflection
[Summary]

### Ecosystem Updates
[List any documentation, commands, hooks, workflows, skills, prompts or templates updated]

### Technical Debt
[Remaining items]

### Commits
[Git log]

### Final Status
- Tests: PASS / FAIL
- Lint: PASS / FAIL
- Hooks: PASS / FAIL
- Repository Ready: YES / NO
```
