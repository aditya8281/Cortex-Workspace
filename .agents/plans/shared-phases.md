# Shared Execution Phases

This document defines reusable phases that multiple commands reference. Commands include a one-line reference to a phase here rather than duplicating its instructions.

**Purpose:** Eliminate duplicate instructions across the command ecosystem. Update phases here, and every referencing command stays consistent.

---

## Phase: Repository Intelligence

Used by: `/project:develop` S1, `/project:prompt` S0-1, `/project:audit` S1, `/project:feature-gap` S1, `/project:release` S1
Referenced as: The orchestrator command's discovery step

### Git State

```bash
git status
git branch --show-current
git log --oneline -10
git stash list 2>/dev/null
```

### Active Development State

```bash
cat .agents/plans/ACTIVE_VERSION.md 2>/dev/null || echo "No ACTIVE_VERSION.md"
grep -r "in_progress\|active\|complete" .agents/plans/versions/*/progress.md 2>/dev/null || true
```

### Repository Structure

```bash
find . -maxdepth 3 -type d | sort | head -40
```

### Test Baseline

```bash
pytest --collect-only 2>&1 | tail -3
```

**Outcome:** Current branch, version, phase, repo structure, and test count known.

---

## Phase: Planning Ecosystem Load

Used by: `/project:enhance_plan` S0, `/project:feature-gap` S1, `/project:release` S1, `/project:update` P0.1
Referenced as: Load planning artifacts

Read:

- `.agents/plans/guide.md` — The constitution: architecture principles, what to build/reject
- `.agents/plans/implementation_steps.md` — Execution order: version phases, deliverables
- `.agents/plans/FinalCompatibilities.md` — ODYSSEUS cross-reference matrix
- `docs/ROADMAP.md` — Public roadmap: version timeline, current status
- Active phase plan: `.agents/plans/versions/v{ACTIVE}/Phase-{N}.md`
- Active progress: `.agents/plans/versions/v{ACTIVE}/progress.md`

Also note:

- Available commands: `ls .claude/commands/project/`
- Available hooks: `ls .claude/hooks/` (if directory exists)
- Available skills: `ls .agents/skills/ | head -20`

**Outcome:** Complete understanding of the planned state — roadmap, versions, phases, deliverables, exit criteria.

---

## Phase: System Validation

Used by: `/project:cortex` P4, `/project:verify`, `/project:audit` S2, `/project:release` S2
Referenced as: Run system validation

### Backend Tests

```bash
make test
```

### Lint

```bash
make lint
```

### Format

```bash
make format --check
```

### Frontend Tests (if frontend exists)

```bash
if [ -f frontend/package.json ]; then cd frontend && npm test; else true; fi
```

### Frontend Build (if frontend exists)

```bash
if [ -f frontend/package.json ]; then cd frontend && npm run build; else true; fi
```

### Hooks

```bash
uv run python .claude/hooks/run_hooks.py 2>/dev/null || python3 .claude/hooks/run_hooks.py 2>/dev/null || echo "No hooks runner found"
```

### Migrations

```bash
make migrate 2>/dev/null || echo "No migration target"
```

Report: pass/fail per check, any failures with details.

**Block merge on any FAIL.**

---

## Phase: Documentation Consistency Check

Used by: `/project:cortex` P5, `/project:reflect` (docs section), `/project:enhance_plan` S3, `/project:release` S4
Referenced as: Check documentation consistency

### Check List

| Check | How |
|-------|-----|
| New/changed APIs reflected in `docs/API.md` | Read `docs/API.md`, check for API changes in code |
| New models reflected in `docs/DATABASE.md` | Read `docs/DATABASE.md`, check for model changes |
| Architecture changes in `docs/ARCHITECTURE.md` | Read `docs/ARCHITECTURE.md`, check for drift |
| ADR created for architectural decisions | Check `docs/decisions/` for relevant ADRs |
| README.md reflects current state | Quick scan of README.md |
| Cross-references valid | Check links in docs reference real files |

### For Each Outdated Document

- What changed in code that the doc doesn't reflect
- Which sections need updating
- Severity: actionable / suggestion / insight

**Outcome:** Every outdated document identified, with recommended updates.

---

## Phase: Engineering Quality Review

Used by: `/project:cortex` P5, `/project:review`
Referenced as: Run engineering quality review

### Correctness

- Missing error handling (bare `except:`, swallowed exceptions)
- Off-by-one errors, null checks, type mismatches
- Race conditions, resource leaks

### API Patterns

- Missing `response_model=` on API endpoint decorators
- Missing ownership checks (`resource.user_id == current_user.id`)
- Routes not in correct order (specific before parameterized)

### Code Quality

- Hardcoded values that should be in config
- Missing docstrings on public functions
- Overly complex logic
- Dead code or unused imports

### Testing

- New functions/classes without tests
- Edge cases not covered
- Missing integration tests for API endpoints

Report findings with severity: P0 (critical) / P1 (important) / P2 (minor).

**Block push on any P0 findings.**

---

## Phase: Architecture Drift Detection

Used by: `/project:cortex` P5, `/project:architecture`, `/project:enhance_plan` S3
Referenced as: Check architecture drift

For each architecture section in `guide.md` §4 (Daemon, Desktop, Memory, Graph, Retrieval, Agent, Workflow, Plugin, CLI, Ecosystem):

- Is the "current approach" description accurate?
- Is the "final decision" still the intended direction?
- Has implementation diverged from documented design?

Also check ADRs in `docs/decisions/`:

- Read `docs/decisions/README.md` for ordering
- For each ADR: verify its decision still reflects the codebase
- Mark superseded ADRs
- Identify undocumented decisions needing new ADRs

Report with status per section: aligned / warn / drift.

---

## Phase: Adversarial Challenge

Used by: `/project:cortex` P5, `/project:challenge`, `/project:update` P5
Referenced as: Run adversarial challenge

Challenge the plan/implementation across these dimensions:

### Risks and Failure Modes
- What could go wrong?
- Single points of failure?
- Behavior under load/error conditions?

### Edge Cases
- Boundary conditions not handled?
- Empty inputs, large inputs, concurrent access?
- External service unavailable?

### Over/Under-Engineering
- More complex than needed?
- Too simple for requirements?
- Simpler approaches that achieve same goal?

### Wrong Assumptions
- What assumptions might be incorrect?
- What would invalidate this approach?

### Version Boundaries
- Belongs in current version or scope creep from later version?

### CORTEX Principle Alignment
- Privacy-first, compound learning, graceful degradation, model freedom?

Report with severity per challenge: critical / warning / nit.

**Challenges are advisory — they inform, not block.**

---

## Phase: Post-Completion Reflection

Used by: `/project:cortex` P6, `/project:reflect`, `/project:develop` S5
Referenced as: Run post-completion reflection

### Identify Work Completed

```bash
git diff --stat HEAD~1
```

Summarize: files changed, features, fixes, refactors, tests, docs.

### Quality
Code cleanliness, error handling, edge cases, naming, comments.

### Redundancy
Duplication across files, consolidation opportunities, repeated literals.

### Automation
Manual steps remaining, Make target opportunities, hook candidates.

### Skill/Hook/Workflow Opportunities
New reusable patterns, automation candidates, documentation gaps.

### Documentation Gaps
Every file under `docs/` checked against code changes. Outdated docs identified.

### Technical Debt
TODOs, shortcuts, postponed refactors, known limitations.

### Test Gaps
Missing coverage, edge cases not tested, integration test gaps.

### Consistency
Naming, formatting, error handling, typing patterns across the codebase.

### Regression Risk
Dependencies, integration points, backward compatibility concerns.

### Ecosystem Impact
Commands, hooks, workflows, skills needing updates.

### Output

```text
| # | Category | Severity | Finding | Recommendation |
|---|----------|----------|---------|----------------|
| 1 | quality | action-item | ... | ... |
```

Severity: insight (observation) / suggestion (worth considering) / action-item (should complete).

Save report to `docs/audits/YYYY-MM-DD-reflect-{N}.md` if any action-item exists.

---

## Phase: Repository Cleanup

Used by: `/project:cortex` P7, `/project:develop` (post-execution)
Referenced as: Clean up repository

### Review Changes

```bash
git status
git diff --name-only main
```

### Remove

- Temporary files
- Abandoned implementations
- Dead code
- Obsolete comments
- Scratch files
- Stale references

### Verify

- Imports are clean
- Documentation references valid
- Configuration consistent
- No TODO/FIXME left intentionally
- No stale branches

**Outcome:** Only intentional changes remain.

---

## Phase: Version Integration Check

Used by: `/project:cortex` P8, `/project:release`
Referenced as: Verify version integration readiness

### Pre-Merge Gate

- [ ] System validation passes (tests, lint, format, hooks, build)
- [ ] Documentation consistent with changes
- [ ] ADRs created for architectural decisions
- [ ] Progress tracking updated
- [ ] Clean commit history
- [ ] Working tree clean

### Merge

```bash
make hooks-merge && make check
```

**Only finalize when all gates pass.**

---

## Phase: Repository Health Scan

Used by: `/project:health`, `/project:improve`
Referenced as: Run repository health scan

### Hook Health

```bash
uv run python .claude/hooks/run_hooks.py 2>/dev/null || python3 .claude/hooks/run_hooks.py 2>/dev/null
```

Report: pass/fail per hook, any false positives.

### Skill Health

- List all skills in `.agents/skills/`
- Check for definition files in each
- Flag skills not updated in 30+ days as stale
- Flag skills with no references in docs/workflows as unused

### Tech Debt Hotspots

```bash
git log --oneline --since="2 weeks ago" | head -30
```

- Files changed 5+ times in recent commits
- TODO/FIXME/HACK count across codebase
- Files with most tech debt indicators

### Documentation Freshness

Check each doc in `docs/` for:
- "Last updated" date
- Outdated references
- Broken cross-references

**Outcome:** Health status across hooks, skills, tech debt, documentation.
