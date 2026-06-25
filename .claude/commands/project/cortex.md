# /project:cortex — Autonomous Development Iteration

Run this command to execute one complete development cycle. It reads the repository state, plans the work, implements it, validates, reviews, cleans up, and commits — all autonomously.

Only ask the human when a decision would change architecture, vision, or product direction.

## Instructions

### Phase 0: CONTEXT

Read all repository state before doing anything:

```bash
# Constitution and architecture
cat .agents/plans/guide.md

# Execution plan
cat .agents/plans/implementation_steps.md

# Active version and phase
cat ACTIVE_VERSION.md
grep -r "in_progress\|active" .agents/plans/versions/*/progress.md

# Recent work
git log --oneline -10
git status
git branch --show-current

# Current health
make check
```

Read the active phase plan: `.agents/plans/versions/vX/Phase-N.md` (replace X with active version).

Summarize: Where is the repo? What version/phase? What's the next piece of work? What's the current test/lint status?

### Phase 1: PLAN (Critical Thinking)

Determine what work should be done in this iteration.

**When a plan exists (phase plan covers next work):**
- Read the plan thoroughly
- **Challenge every step:** Is this still the best approach? Are assumptions valid given current repo state? Has anything changed since the plan was written?
- **Adapt:** If a better approach emerges during planning, use it. Note the deviation and why.
- **Question scope:** Is the plan too broad for one iteration? Too narrow? Should it be split?
- **Verify file targets:** Do the files the plan references still exist? Have they been modified?
- **Assess dependencies:** Does the plan account for all integration points?

**When no plan exists:**
- Determine what work is needed from context (recent commits, open issues, roadmap position)
- Create a brief plan before proceeding
- Apply the same critical thinking

**The plan is guidance, not gospel. Your judgment supersedes the plan when you can articulate why.**

Select applicable skills from `.agents/skills/`. If the work involves complex design, consider whether the brainstorming skill should be invoked.

Define exit criteria for this iteration:
- What specific deliverables will be produced?
- What tests must pass?
- What validation must succeed?

### Phase 2: BRANCH

```bash
git checkout -b feat/<topic>
```

Verify clean starting state: `git status` shows only expected changes.

### Phase 3: BUILD

Implement the planned work:

1. Follow TDD when applicable — write test, verify fail, implement, verify pass
2. Commit after each logical unit with descriptive messages
3. After each commit, run:
   ```bash
   make lint && make format
   ```
4. Run relevant tests after each commit:
   ```bash
   make test
   ```
5. For multi-file work, use subagents when beneficial
6. Leverage MCP servers (context7 for library docs) where appropriate

**If you discover a better approach during implementation than what the plan specified:**
- Use the better approach
- Document the deviation in the commit message
- Update the plan if the deviation is significant

### Phase 4: VALIDATE

Run the full validation suite:

```bash
make test                    # Backend tests
cd frontend && npm test      # Frontend tests
make lint                    # Linting
make format --check          # Format check
make hooks-onchange          # Hook suite
```

If anything fails: fix the issue and loop back to Phase 3. Do not proceed with failures.

### Phase 5: REVIEW

**Code quality review:**
- Review each changed file for correctness, patterns, completeness
- Check: error handling, API patterns (response_model=, ownership checks), code quality, test coverage
- Address all P0 (critical) and P1 (important) findings

**Adversarial review (if architectural decision involved):**
- Challenge the approach: risks, edge cases, over/under-engineering, wrong assumptions
- Verify alignment with CORTEX principles: privacy-first, compound learning, two-tier trust, graceful degradation, model freedom, living knowledge

If critical issues found: loop back to Phase 3 to fix.

### Phase 6: REFLECT

Run through the reflection framework:

1. **Quality:** Could any code be cleaner? Functions doing too much? Names clear?
2. **Redundancy:** Anything duplicated? Patterns that could share utilities?
3. **Automation:** Any manual steps that could be automated?
4. **Skill/Hook/Workflow Opportunity:** Should any finding become a new skill, hook, or workflow?
5. **Future Problems:** Does this introduce technical debt? Will it scale poorly?
6. **Documentation Gap:** Anything undocumented that should be?

Update tracking:
- Update `progress.md` with completed components
- Update relevant docs if architecture changed
- Check if new ADR is needed (new technology, architecture pattern, security policy, API design)

### Phase 7: CLEANUP

After reflection, before final commit:

1. Identify files created during this iteration that are unnecessary:
   ```bash
   git status
   git diff --name-only main
   ```
2. Remove any scratch files, temp outputs, abandoned approaches
3. Check for new TODO/FIXME introduced — resolve or document them
4. Verify no stale references to removed files exist in docs or imports
5. Confirm only intended files are staged

### Phase 8: COMMIT

1. Verify commit messages are meaningful and follow conventions
2. Run the merge gate:
   ```bash
   make hooks-merge
   ```
3. Verify repository is ready for merge:
   ```bash
   make check
   ```

### Exit Gate

After Phase 8, verify all exit criteria:

- [ ] All tests pass (`make test` + `cd frontend && npm test`)
- [ ] Lint clean (`make lint`)
- [ ] No P0/P1 review findings unresolved
- [ ] Progress tracking updated
- [ ] Cleanup complete — no unnecessary files

**If exit criteria not met:** Loop back to Phase 3. Maximum 3 iterations before escalating to human.

### Escalation to Human

Pause and ask the user when:
- A decision would change architecture, vision, or product direction
- Multiple valid paths exist with no clear winner
- Maximum loop iterations exceeded
- Unexpected blocker that cannot be resolved autonomously
- Scope ambiguity that the repository cannot resolve

## Output

Report when complete:

```
## Cortex Iteration: [date]

### Context
[What was the starting state]

### Work Done
[What was implemented, fixed, or changed]

### Files Changed
[List of files modified/created/deleted]

### Validation
[PASS/FAIL for each check]

### Review
[Findings and resolution]

### Reflection
[Key observations, action items]

### Commits
[Git log of commits made in this iteration]

### Status
- Tests: PASS/FAIL
- Lint: PASS/FAIL
- Hooks: PASS/FAIL
- Ready for merge: YES/NO
```
