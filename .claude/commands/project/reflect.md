# /project:reflect — Reflection Framework

Before completing any major task, run through this reflection framework systematically.

## Instructions

### 1. Identify the work just completed.

Run:

```bash
git diff --stat HEAD~1
```

Summarize:

* Files modified
* Features implemented
* Bugs fixed
* Refactors performed
* Tests added or updated
* Documentation updated

---

### 2. Run through the reflection framework.

For every section below:

* Analyze the actual implementation and repository state.
* Base findings on the code, not assumptions.
* Prefer concrete evidence over abstract observations.

---

## Quality

* Could any code be cleaner, simpler, or more readable?
* Are there functions that do too much?
* Are responsibilities well separated?
* Are variable, class, and function names descriptive?
* Is error handling comprehensive?
* Are edge cases handled?
* Are comments accurate and useful?

---

## Redundancy

* Is anything duplicated that could be consolidated?
* Are similar implementations scattered across files?
* Could utilities be extracted?
* Are repeated literals better represented as constants?
* Are similar abstractions duplicated?

---

## Automation

* Is any manual step still required?
* Could repetitive commands become Make targets or scripts?
* Should repetitive validation become hooks?
* Could CI automate any of this work?

---

## Skill Opportunity

* Could this workflow become a reusable skill?
* Is this a Cortex-specific process?
* Would documenting this prevent future mistakes?
* Should an existing skill be expanded?

---

## Hook Opportunity

* Should any validation become a hook?
* Could a hook detect this earlier?
* Should it run on save, commit, push, or release?
* Should an existing hook be updated?

---

## Workflow Opportunity

* Does this reveal a new workflow?
* Should an existing workflow be updated?
* Is there a missing workflow?
* Should `docs/WORKFLOWS.md` change?

---

## Command Opportunity

Review `.claude/commands/project/`.

Determine whether:

* Existing commands require updates.
* Examples are outdated.
* Instructions no longer match implementation.
* New commands should be created.
* Existing commands should be merged, split, or extended.
* Command execution order should change.
* Help text or descriptions should improve.

Explicitly list every command requiring updates.

---

## Future Problems

* What downstream issues could this introduce?
* What technical debt was created?
* What might not scale?
* What assumptions could later fail?

---

## Future Opportunities

* What capabilities does this enable?
* What future features become possible?
* Could this compose with existing functionality?
* Could it become reusable elsewhere?

---

## Documentation Gap

Identify anything undocumented.

Review whether implementation requires updates to:

* README.md
* CLAUDE.md
* AGENT.md
* PRODUCT.md
* DESIGN.md
* ARCHITECTURE.md
* CHANGELOG.md
* API documentation
* onboarding guides
* migration guides
* examples
* every file under `docs/`
* every plan under `docs/plans/`
* every audit under `docs/audits/`
* every workflow document
* every design document
* every architecture document
* every source-of-truth document

For every outdated document:

* Explain why.
* Identify affected sections.
* Recommend updates.
* Assign severity.

Always compare documentation against the implementation—not intended behavior.

---

## Source of Truth Audit

Review the repository's canonical sources of truth.

Verify consistency between implementation and:

* Documentation
* Architecture
* Product definition
* Design documents
* Commands
* Hooks
* Workflows
* Skills
* Prompts
* Templates
* Configuration
* Examples
* Tests

Do not assume unchanged files remain correct.

---

## Ecosystem Growth

Determine whether any finding should become:

* New Skill
* Updated Skill
* New Hook
* Updated Hook
* New Workflow
* Updated Workflow
* New Command
* Updated Command
* New Prompt
* Updated Prompt
* New Template
* Updated Template
* New Documentation
* Updated Documentation

Prefer improving existing ecosystem components before creating new ones.

---

## Configuration Audit

Review whether implementation requires updates to:

* settings.json
* package.json
* pyproject.toml
* requirements.txt
* lockfiles
* Dockerfiles
* docker-compose
* GitHub Actions
* CI/CD
* editor configuration
* lint configuration
* formatter configuration
* MCP configuration
* Claude configuration
* environment examples
* build scripts

---

## Architecture Review

Evaluate:

* Coupling
* Cohesion
* Dependency graph
* Module responsibilities
* Layer separation
* Abstraction quality
* Scalability
* Maintainability

---

## Performance Review

Review for:

* unnecessary allocations
* repeated filesystem access
* repeated network requests
* blocking operations
* inefficient algorithms
* memory usage
* caching opportunities

---

## Security Review

Review for:

* validation
* authorization
* authentication
* secret handling
* filesystem safety
* subprocess safety
* dependency risks
* sensitive logging
* unsafe defaults

---

## Maintainability Review

Determine:

* hardest code to maintain
* confusing implementations
* poor naming
* overly large modules
* unnecessary complexity
* onboarding friction

---

## Agent Compatibility

Would future AI agents easily:

* discover
* understand
* modify
* extend
* debug
* reuse

this implementation?

Identify anything likely to confuse future agents.

---

## Knowledge Capture

Should this become:

* coding standard
* architecture decision
* reusable pattern
* design principle
* reusable checklist
* prompt
* template
* documentation snippet
* example
* reusable skill

Specify exactly where knowledge should be stored.

---

## Consistency Audit

Review consistency of:

* naming
* folder structure
* architecture
* formatting
* logging
* error handling
* typing
* comments
* documentation
* testing
* configuration
* prompts
* commands
* workflows
* hooks
* skills

---

## Regression Risk

Review:

* direct dependencies
* indirect dependencies
* integration points
* backward compatibility
* existing workflows
* existing commands
* public APIs

Identify anything this change could unintentionally break.

---

## Technical Debt

Identify:

* shortcuts
* TODOs
* postponed refactors
* temporary implementations
* known limitations

Estimate future cost if unresolved.

---

## Test Gap

* Is any behavior untested?
* Are edge cases covered?
* Should unit tests be added?
* Should integration tests be added?
* Should end-to-end tests be added?
* Should regression tests be added?

---

## Repository Consistency Sweep (Mandatory)

Inspect the repository beyond modified files.

Explicitly review:

* implementation
* architecture
* documentation
* commands
* hooks
* workflows
* skills
* prompts
* templates
* configuration
* automation
* examples
* tests

Review every relevant command under:

```
.claude/commands/project/
```

Review every relevant document under:

```
docs/
```

Determine whether any file outside the modified set should also be updated.

Do **not** assume repository consistency simply because files were not modified.

---

### 3. Assign severity to every finding.

Use exactly one:

* **insight** — observation, no action needed
* **suggestion** — worth considering, not urgent
* **action-item** — should be completed

---

### 4. Output structured findings.

```text
## Reflection: [date]

### Findings

| # | Category | Severity | Finding | Recommendation |
|---|----------|----------|---------|----------------|
| 1 | quality | action-item | ... | ... |

### Summary

- Insights: N
- Suggestions: N
- Action Items: N

### Ecosystem Follow-up

#### Commands
- Existing commands requiring updates
- New commands to create

#### Workflows
- Existing workflows requiring updates
- New workflows to create

#### Hooks
- Existing hooks requiring updates
- New hooks to create

#### Skills
- Existing skills requiring updates
- New skills to create

#### Prompts
- Existing prompts requiring updates
- New prompts to create

#### Templates
- Existing templates requiring updates
- New templates to create

#### Documentation
- Files requiring updates

#### Configuration
- Files requiring updates

#### Tests
- Tests to add

#### Repository Review
- Files outside the modified set requiring updates
```

---

### 5. Save report.

If any **action-item** exists:

Save the report to:

```text
docs/audits/YYYY-MM-DD-reflect-{N}.md
```

Where:

* `YYYY-MM-DD` is today's date.
* `{N}` is the reflection number for that day.

---

### 6. Final Verdict

Conclude with:

* Overall quality score (1–10)
* Release readiness

  * Ready
  * Ready with follow-ups
  * Needs revision
* Top five highest-priority action items

---

### 7. Completion Checklist

Before finishing, explicitly confirm:

* ✓ Every relevant documentation source was reviewed against the current implementation.
* ✓ Every relevant file under `docs/` was considered where applicable.
* ✓ Every relevant command under `.claude/commands/project/` was reviewed for required updates.
* ✓ Hooks were reviewed.
* ✓ Skills were reviewed.
* ✓ Workflows were reviewed.
* ✓ Prompts were reviewed.
* ✓ Templates were reviewed.
* ✓ Configuration files were reviewed.
* ✓ Tests were reviewed.
* ✓ Repository consistency beyond modified files was evaluated.
* ✓ All recommended ecosystem improvements were listed.
* ✓ Reflection is based on the current codebase state rather than assumptions.
