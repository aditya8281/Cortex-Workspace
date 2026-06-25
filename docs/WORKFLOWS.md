# CORTEX Workflow Definitions

This document defines all workflows for the CORTEX development process.

---

## 1. Development Lifecycle

### Stages

```
Branch → Skill Discovery → Triage → Plan → Build → Review → Reflect → Release
```

### Stage 1: Branch First

**Purpose:** Create a feature branch before any work begins. `main` must always be in a working state.

**Steps:**
1. Agent creates a branch from `main`: `git checkout -b feat/<topic>`
2. Agent follows branch naming convention: `feat/`, `fix/`, `docs/`, `refactor/`
3. All work happens on the branch
4. After verification, agent merges back to `main` with `--no-ff`
5. Agent deletes the feature branch

**Gate:** Branch exists. No direct commits to `main`.

**Parallel branch limit:** Max 2-3 active branches. Finish one before starting the next.

### Stage 2: Skill Discovery

**Purpose:** Before any work, determine if existing skills can improve the process.

**Steps:**
1. Agent identifies the task domain
2. Agent searches for relevant skills (system-reminder skill list, `.agents/skills/`)
3. Agent evaluates available skills against the task
4. Agent selects the best skill or skill combination
5. Agent applies those skills before continuing

**Gate:** Skill discovery completed. If no skill applies, document why (may become a skill creation candidate).

**Rule:** Context → Find Skill → Use Skill → Brainstorm → Plan → Implement → Test → Validate → Review → Complete. NOT: Context → Implement Immediately.

### Stage 3: Triage

**Purpose:** Classify and prioritize incoming work.

**Steps:**
1. Agent reads the request
2. Agent checks: Is this in the roadmap? Existing ADR? Conflicts?
3. Agent classifies: Feature / Bug / Refactor / Docs / Audit
4. Agent assigns priority: P0 (broken) / P1 (security) / P2 (important) / P3 (nice)
5. Agent asks human if classification is ambiguous

**Gate:** Classification agreed before proceeding.

### Stage 4: Plan

**Purpose:** Create specification and get human approval.

**Steps:**
1. Agent identifies affected files and systems
2. Agent determines which skills apply
3. Agent assesses blast radius
4. Agent creates spec (using brainstorming skill for complex work)
5. Agent creates ADR if architectural decision needed
6. Agent presents spec to human for approval

**Gate:** Human approves spec. Agent MUST NOT implement until approved.

### Stage 5: Build

**Purpose:** Implement the approved spec.

**Steps:**
1. Agent follows TDD if skill requires it
2. Agent commits after each logical unit
3. Agent runs `make lint` + `make format` after each commit
4. Agent runs relevant tests after each commit
5. If >3 files touched, agent considers splitting into sub-agents

**Gate:** All tests pass, lint clean, build succeeds.

### Stage 6: Review

**Purpose:** Verify quality and correctness.

**Steps:**
1. Agent runs `/project:review` for code quality analysis
2. Agent runs `/project:challenge` for adversarial review (if architectural decision)
3. Agent runs code-review skill for correctness
4. Agent runs simplify skill for quality
5. Agent verifies each finding independently
6. Agent addresses P0/P1 findings
7. Agent presents review results to human

**Gate:** No P0/P1 findings, no regressions, build passes.

### Stage 7: Reflect & Release

**Purpose:** Final validation and merge.

**Steps:**
1. Agent runs `/project:reflect` for reflection framework
2. Agent runs full `make check` + `npm run build`
3. Agent updates changelog if user-facing change
4. Agent creates PR with clear description
5. Human reviews and approves
6. Agent merges

**Gate:** All validation passes, human merges.

**Command equivalents:**
- Code quality: `/project:review`
- Adversarial: `/project:challenge`
- Reflection: `/project:reflect`
- Verification: `/project:verify`
- Release readiness: `/project:release`

---

## 2. Bug-Finding Workflow

### Automatic Bug Discovery

**Trigger:** Code changes or scheduled audit

**Process:**
1. Agent scans changed files for common patterns
2. Agent checks for security vulnerabilities
3. Agent checks for logic errors
4. Agent checks for edge cases
5. Agent reports findings with severity

**Severity levels:**
- **Critical:** Data loss, security breach, system crash
- **High:** Feature broken, data corruption possible
- **Medium:** Feature degraded, workaround exists
- **Low:** Cosmetic issue, minor inconvenience

**Output:** Findings in `docs/audits/YYYY-MM-DD-report.md`

### Manual Bug Report

**Trigger:** User reports bug

**Process:**
1. Agent reproduces the bug
2. Agent identifies root cause
3. Agent creates fix
4. Agent adds regression test
5. Agent documents fix in audit report

---

## 3. Validation Workflow

### Pre-commit Validation

**Trigger:** Every git commit

**Checks:**
- ruff lint + format (Python)
- trailing whitespace removal
- YAML/TOML validation
- large file detection
- secret detection

**Enforcement:** Blocks commit if any check fails.

### Local Validation

**Trigger:** Before push

**Checks:**
- `make lint` — ruff + mypy
- `make format` — ruff format
- `make test` — backend pytest
- `cd frontend && npm test` — frontend vitest
- `cd frontend && npm run build` — frontend build

**Enforcement:** Agent runs before pushing.

### CI Validation

**Trigger:** Push or PR creation

**Checks:**
- Backend: ruff lint, mypy, pytest
- Frontend: next lint, tsc, vitest, build
- Full test suite with services

**Enforcement:** Blocks merge if any check fails.

### Post-merge Validation

**Trigger:** Weekly schedule or manual

**Checks:**
- Architecture drift detection
- Documentation drift detection
- Technical debt identification
- Dead code detection
- Placeholder detection

**Enforcement:** Reports findings, tracks resolution.

---

## 4. Review Workflow

### Code Review

**Trigger:** PR creation or manual request

**Process:**
1. Agent reads PR diff
2. Agent checks correctness (logic, edge cases, security)
3. Agent checks quality (naming, structure, patterns)
4. Agent checks completeness (tests, docs, error handling)
5. Agent reports findings with severity
6. Agent verifies each finding independently
7. Agent addresses findings
8. Human approves

**Finding format:**
```
path:line: <emoji> <severity>: <problem>. <fix>.
```

### Adversarial Verification

**Process:**
1. Agent proposes finding
2. Independent agent tries to refute finding
3. If refuted, finding is discarded
4. If confirmed, finding is reported
5. Multiple verifiers for critical findings

---

## 5. Refactoring Workflow

### When to Refactor

- Code duplication detected
- Complexity exceeds threshold
- Pattern inconsistency
- Performance bottleneck identified
- Security improvement needed

### Refactoring Process

1. Agent identifies refactoring target
2. Agent creates refactoring plan
3. Agent ensures test coverage before refactoring
4. Agent performs refactoring in small steps
5. Agent runs tests after each step
6. Agent verifies no regressions
7. Agent updates documentation if patterns changed
8. Human reviews

### Refactoring Rules

- Never refactor and add features simultaneously
- Always have tests before refactoring
- Refactoring must not change external behavior
- Each refactoring step must be independently committable
- If refactoring introduces bugs, revert immediately

---

## 6. Release Workflow

### Pre-release Checklist

1. All tests pass
2. All linting passes
3. All builds succeed
4. All CI checks pass
5. No open P0/P1 bugs
6. Documentation updated
7. Changelog updated
8. ADRs created for architectural changes

### Release Process

1. Agent creates release branch
2. Agent runs full validation suite
3. Agent updates version numbers
4. Agent updates changelog
5. Agent creates PR
6. Human reviews and approves
7. Agent merges to main
8. Agent creates git tag
9. Agent archives completed audit findings

### Post-release

1. Agent monitors for issues
2. Agent documents any hotfixes
3. Agent updates roadmap with completed items
4. Agent archives completed phase

---

## 7. Audit Workflow

### Scheduled Audit

**Frequency:** Weekly

**Process:**
1. Agent scans codebase for issues
2. Agent checks architecture drift
3. Agent checks documentation drift
4. Agent identifies technical debt
5. Agent finds dead code
6. Agent finds duplicate code
7. Agent finds incomplete features
8. Agent finds placeholders (TBD, TODO, FIXME)
9. Agent creates audit report
10. Agent prioritizes findings
11. Human reviews and approves action plan

### On-demand Audit

**Trigger:** Manual request or before release

**Process:** Same as scheduled audit, but scoped to specific area.

### Audit Report Format

```markdown
# Audit Report: YYYY-MM-DD

## Summary
- Total findings: N
- Critical: N
- High: N
- Medium: N
- Low: N

## Findings

### [SEVERITY] Finding title
- **File:** path/to/file.py:line
- **Description:** What's wrong
- **Impact:** What could happen
- **Fix:** How to fix it
- **Status:** Open | In Progress | Fixed
```

---

## 8. Documentation Workflow

### When to Update Docs

| Change | Doc to Update |
|--------|--------------|
| New API endpoint | docs/API.md |
| New database table | docs/DATABASE.md |
| New security pattern | docs/SECURITY.md |
| Architecture change | docs/ARCHITECTURE.md |
| Roadmap change | docs/ROADMAP.md |
| New decision | docs/decisions/NNN-name.md |
| Bug found | docs/audits/YYYY-MM-DD-report.md |
| Workflow change | docs/WORKFLOWS.md |
| Governance change | docs/GOVERNANCE.md |

### Documentation Process

1. Agent identifies doc that needs update
2. Agent reads current doc
3. Agent makes targeted update
4. Agent updates "Last updated" date
5. Agent commits with docs: prefix

### Documentation Standards

- Use Markdown with consistent heading levels
- Include "Last updated" date at top
- Use tables for structured data
- Use code blocks for commands/examples
- Cross-reference related docs with relative links

---

## 9. Skill Creation Workflow

### When to Create a Skill

| Trigger | Action |
|---------|--------|
| Repetitive process identified | Extract into skill |
| CORTEX-specific workflow matured | Convert to skill |
| Agent discovers a better workflow | Improve existing skill or create new one |
| Skill gap detected during execution | Create skill improvement candidate |

### Skill Creation Process

1. **Extract:** Document the process step-by-step
2. **Document:** Write skill definition with purpose, steps, examples, validation
3. **Create:** Add to `.agents/skills/your-skill/`
4. **Test:** Run the skill on a real task
5. **Validate:** Verify output quality, identify friction points
6. **Integrate:** Update workflows to reference the new skill
7. **Commit:** Add with `feat:` prefix

### Skill Quality Standards

- Clear purpose statement
- Step-by-step instructions
- At least one concrete example
- Validation steps (how to verify the skill worked)
- Error handling guidance
- References to related skills

### CORTEX-Specific Skill Candidates

- **CORTEX Architecture Audit:** Validate architecture against docs/ARCHITECTURE.md
- **CORTEX Repository Health Review:** Run full health check suite
- **CORTEX Planning Consistency Audit:** Verify roadmap matches implementation
- **CORTEX Documentation Consistency Audit:** Check all doc links and references
- **CORTEX Frontend/Backend Contract Audit:** Verify API contract integrity
- **CORTEX Release Readiness Audit:** Pre-release validation checklist

---

## 10. Skill Evolution Workflow

### When to Evolve a Skill

- After every 5 uses (review effectiveness)
- When output quality degrades
- When missing steps are discovered
- When friction points are identified
- When CORTEX architecture changes

### Evolution Process

1. **Review:** Analyze recent skill executions
2. **Identify:** Missing steps, friction points, outdated references
3. **Improve:** Update skill definition
4. **Test:** Run improved skill on a real task
5. **Document:** Record what changed and why
6. **Commit:** Add with `improve:` prefix

### Skill Health Metrics

| Metric | Target |
|--------|--------|
| Usage frequency | >5 uses per month for active skills |
| Success rate | >90% of executions produce good output |
| Friction score | <2 manual corrections per execution |
| Staleness | Updated within last 30 days |

### Skill Retirement

When a skill is no longer useful:

1. Document why it's being retired
2. Remove from `.agents/skills/`
3. Update any workflows that reference it
4. Commit with `remove:` prefix
