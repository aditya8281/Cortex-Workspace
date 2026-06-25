## Instructions

### Phase 0: REPOSITORY INTELLIGENCE

Before making any decisions, build an accurate understanding of the current repository.

Inspect:

```bash
# Repository
pwd
git status
git branch --show-current
git log --oneline -10

# Repository health
make check

# Repository structure
find . -maxdepth 3 -type d | sort
find . -maxdepth 2 -type f | sort

# Constitution
cat .agents/plans/guide.md

# Execution plan
cat .agents/plans/implementation_steps.md

# Active version
cat .agents/plans/ACTIVE_VERSION.md
grep -r "in_progress\|active" .agents/plans/versions/*/progress.md
```

Read, where present:

* README.md
* CLAUDE.md
* AGENT.md
* DESIGN.md
* .agents/
* docs/
* docs/ARCHITECTURE.md
* docs/WORKFLOWS.md
* docs/GOVERNANCE.md
* Active phase document
* Relevant ADRs
* Relevant architecture decisions

Discover:

* repository layout
* active version
* active phase
* current roadmap position
* completed work
* in-progress work
* current blockers
* repository health
* existing commands
* existing hooks
* existing workflows
* existing skills
* existing prompts
* existing templates

Also identify existing implementations related to the task.

Prefer extending existing code over introducing parallel implementations.

Produce a concise repository intelligence summary before continuing.

---

### Phase 1: STRATEGIC PLANNING

Determine the highest-value work for this iteration.

When an implementation plan exists:

* Read it completely.
* Challenge every assumption.
* Verify file locations.
* Verify dependencies.
* Verify integration points.
* Determine whether the plan is still optimal.
* Adapt when a better solution exists.
* Document significant deviations.

When no implementation plan exists:

Create one before implementation.

Do not blindly follow documentation.

Repository state always overrides stale plans.

Determine:

* objectives
* deliverables
* affected modules
* affected APIs
* affected commands
* affected hooks
* affected workflows
* affected skills
* affected documentation
* affected configuration
* affected tests
* dependencies
* risks
* validation strategy
* rollback strategy
* completion criteria

Select applicable skills.

If brainstorming or architecture exploration would materially improve the solution, invoke the appropriate skill before implementation.

Only ask the user when multiple valid architectural directions exist with no objectively better choice.

---

### Phase 2: BRANCH

Create an isolated working branch when appropriate.

```bash
git checkout -b <update type eg. fix,feat etc>/<topic>
```

Verify:

* working tree is clean
* branch naming follows conventions
* repository is ready for implementation

---

### Phase 3: IMPLEMENTATION LOOP

Implement using small, verifiable iterations.

For every logical unit of work:

1. Plan the smallest complete increment.
2. Implement.
3. Follow TDD where practical.
4. Perform a quick self-review.
5. Run relevant linting and tests.
6. Fix issues immediately.
7. Continue.

During implementation:

* Prefer extending existing implementations.
* Avoid duplicated logic.
* Maintain architecture consistency.
* Keep commits logical and atomic.
* Update documentation whenever implementation changes behavior.
* Update configuration when required.
* Use subagents when beneficial.
* Leverage MCP servers where appropriate.

If a substantially better implementation is discovered:

* Prefer the better implementation.
* Explain the deviation.
* Update planning artifacts when necessary.

Repeat until implementation objectives are complete.

---

### Phase 4: SYSTEM VALIDATION

Validate the complete implementation.

Run all applicable validation:

```bash
make test
cd frontend && npm test
make lint
make format --check
make hooks-onchange
```

Also verify:

* integration points
* documentation consistency
* configuration consistency
* public APIs
* generated artifacts
* developer workflows
* backward compatibility where applicable

If any validation fails:

* fix immediately
* repeat validation

Do not proceed until validation succeeds.

---

### Phase 5: ENGINEERING REVIEW

Review implementation from multiple engineering perspectives.

Review:

* correctness
* architecture
* maintainability
* readability
* performance
* security
* scalability
* repository consistency

Check:

* error handling
* abstractions
* duplication
* coupling
* naming
* API design
* ownership boundaries
* test quality

Challenge assumptions.

Identify:

* over-engineering
* under-engineering
* unnecessary complexity
* future maintenance risks

Resolve every P0 and P1 issue before continuing.

Document important P2 improvements for future work.

If significant issues are found:

Return to the Implementation Loop.

---

### Phase 6: REFLECTION

Run the complete Reflection Framework defined in:

`.claude/commands/project/reflect.md`

Apply any action items that belong in the current iteration.

Only defer work when there is a justified reason.

Update:

* progress tracking
* architecture documentation
* ADRs
* implementation plans

when required.

---

### Phase 7: REPOSITORY CLEANUP

Restore repository cleanliness.

Review:

```bash
git status
git diff --name-only main
```

Remove:

* temporary files
* abandoned implementations
* dead code
* obsolete comments
* scratch files
* stale references

Verify:

* imports
* documentation
* configuration
* examples
* references
* TODO/FIXME entries

Ensure only intentional changes remain.

---

### Phase 8: VERSION INTEGRITY

Prepare the repository for integration.

Verify:

* commit quality
* atomic commit history
* meaningful commit messages
* merge readiness

Run:

```bash
make hooks-merge
make check
```

Only finalize the iteration when repository integrity is confirmed.

---

## Exit Gate

The iteration is complete only when all of the following are true:

* [ ] Objectives completed
* [ ] Validation passed
* [ ] Engineering review completed
* [ ] Reflection completed
* [ ] Documentation updated where required
* [ ] Configuration updated where required
* [ ] Progress tracking updated
* [ ] Repository cleanup completed
* [ ] Repository ready for merge

If any requirement is not satisfied:

Return to the Implementation Loop.

Maximum three full iteration loops before escalating.

---

## Escalation Policy

Pause and ask the user only when:

* architecture would change
* product direction would change
* roadmap direction would change
* repository contains conflicting sources of truth
* requirements remain ambiguous after repository analysis
* multiple equally valid architectural solutions exist
* implementation would require unsafe migration
* maximum autonomous iterations have been exceeded
* a blocker cannot be resolved using repository context

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
