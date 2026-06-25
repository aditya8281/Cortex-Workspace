# Command Ecosystem Refactor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing 7 standalone commands with a 13-command ecosystem: a master orchestrator, a prompt generator, 4 new expert commands, 7 refined existing commands, and a quick guide.

**Architecture:** Three-tier design. Tier 1: `/cortex` (autonomous orchestrator). Tier 2: `/prompt` (ecosystem-aware prompt generator). Tier 3: 11 expert commands (standalone, reusable). No command calls another. `/cortex` implements equivalent workflows internally. All commands are markdown files in `.claude/commands/project/`.

**Tech Stack:** Markdown command files (`.claude/commands/project/*.md`), existing governance (CLAUDE.md, AGENTS.md), existing workflows (docs/WORKFLOWS.md), existing hooks, skills, and planning systems.

## Global Constraints

- All commands go in `.claude/commands/project/` (except GUIDE.md which goes in `.claude/commands/`)
- Every command follows structure: Purpose → Instructions → Output format
- No command calls another command programmatically
- `/cortex` implements equivalent workflows internally, not via command chaining
- Commands reference existing systems (skills, hooks, workflows, governance) — never duplicate them
- All file paths referenced in commands must exist in the repository
- Spec location: `docs/superpowers/specs/2026-06-25-command-ecosystem-refactor-design.md`

---

## File Structure

```
Create:
  .claude/commands/project/cortex.md          # Master orchestrator
  .claude/commands/project/prompt.md          # Prompt generator
  .claude/commands/project/audit.md           # Codebase audit
  .claude/commands/project/verify.md          # Verification suite
  .claude/commands/project/release.md         # Release readiness
  .claude/commands/project/feature-gap.md     # Roadmap vs codebase
  .claude/commands/GUIDE.md                   # Quick reference guide

Modify:
  .claude/commands/project/architecture.md    # Add ACTIVE_VERSION.md check
  .claude/commands/project/challenge.md       # Add version boundary check
  .claude/commands/project/health.md          # Clarify scope vs /audit
  .claude/commands/project/ideas.md           # Cross-reference with /feature-gap
  .claude/commands/project/improve.md         # Check for new commands/hooks/skills
  .claude/commands/project/reflect.md         # Check if findings become skills/hooks
  .claude/commands/project/review.md          # Clarify scope vs /verify
  docs/WORKFLOWS.md                           # Update to reference new commands
  CLAUDE.md                                   # Update commands table
```

---

### Task 1: `/cortex` — Master Orchestrator

**Files:**
- Create: `.claude/commands/project/cortex.md`

**Interfaces:**
- Consumes: CLAUDE.md (execution contract), `.agents/plans/guide.md` (constitution), `.agents/plans/implementation_steps.md`, `.agents/plans/versions/vX/Phase-N.md` (active phase), `.agents/plans/versions/vX/progress.md`, `ACTIVE_VERSION.md`, `docs/WORKFLOWS.md`, `docs/GOVERNANCE.md`, `.claude/skills/`, `.claude/hooks/`, `docs/ARCHITECTURE.md`
- Produces: A complete development iteration (branch, implementation, commits, updated tracking)

**Validation:** File exists. Reads correctly. References real file paths. Follows Purpose → Instructions → Output structure. Implements 8 phases from spec. Includes cleanup phase. Includes critical thinking in PLAN phase. Includes exit gate with max 3 iterations. Includes escalation to human.

- [ ] **Step 1: Create `/cortex` command file**

Create `.claude/commands/project/cortex.md` with the following content:

```markdown
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

Select applicable skills from `.claude/skills/`. If the work involves complex design, consider whether the brainstorming skill should be invoked.

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
```

- [ ] **Step 2: Validate file exists and is well-formed**

Run: `cat .claude/commands/project/cortex.md | head -5`
Expected: First line is `# /project:cortex — Autonomous Development Iteration`

Run: `grep -c "Phase" .claude/commands/project/cortex.md`
Expected: 8 or more (Phase 0-8 + Exit Gate + Escalation)

Run: `grep "guide.md\|progress.md\|ACTIVE_VERSION\|WORKFLOWS\|GOVERNANCE\|skills/" .claude/commands/project/cortex.md | wc -l`
Expected: 5+ (references to real ecosystem systems)

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/cortex.md
git commit -m "feat(commands): add /cortex master orchestrator command"
```

---

### Task 2: `/prompt` — Ecosystem-Aware Prompt Generator

**Files:**
- Create: `.claude/commands/project/prompt.md`

**Interfaces:**
- Consumes: Same ecosystem context as /cortex (repo state, roadmap, architecture, skills, hooks, workflows, governance)
- Produces: A generated prompt in a code block, ready for user to use

**Validation:** File exists. References 16 prompt categories. Has self-audit step. References real files/skills/hooks. Doesn't duplicate ecosystem rules.

- [ ] **Step 1: Create `/prompt` command file**

Create `.claude/commands/project/prompt.md` with the following content:

```markdown
# /project:prompt — Ecosystem-Aware Prompt Generator

Generate development prompts that integrate with the Cortex ecosystem. Not a text rewriter — an intelligent prompt architect that understands repo state and routes work through existing systems.

## Instructions

### Step 1: UNDERSTAND

Before generating anything, read the repository state:

```bash
# Current state
git status
git log --oneline -5
git branch --show-current

# Version context
cat ACTIVE_VERSION.md
grep -r "in_progress\|active" .agents/plans/versions/*/progress.md
```

Read these files to understand the ecosystem:
- `docs/ARCHITECTURE.md` — system architecture
- `.agents/plans/guide.md` — constitution and principles
- `docs/WORKFLOWS.md` — development workflows
- `docs/GOVERNANCE.md` — governance rules
- `.claude/skills/` — available skills (list the directory)
- `.claude/commands/project/` — available commands (list the directory)
- `.claude/hooks/` — available hooks

This context ensures generated prompts reference real systems, not hypothetical ones.

### Step 2: CLASSIFY

The user provides a goal (e.g., "implement file watcher integration", "fix the auth bug", "audit the codebase"). Classify it into one of these categories:

| Category | When to Use | Ecosystem Leverage |
|----------|-------------|-------------------|
| **Planning** | Brainstorming or designing a feature | Routes through brainstorming skill, references guide.md principles |
| **Architecture** | Architectural decisions | Routes through /architecture or /challenge, references ADRs |
| **Feature** | Implementing new functionality | Routes through /cortex workflow, references phase plan |
| **Bug Fix** | Diagnosing and fixing bugs | Routes through TDD pattern, references test infrastructure |
| **Audit** | Repository or codebase audit | Routes through /audit, references hooks and automation |
| **Documentation** | Writing or updating docs | References docs/ structure, governance rules |
| **Refactor** | Restructuring code | Routes through /review + /challenge, references architecture |
| **Performance** | Optimization work | References benchmarks, profiling approach |
| **Frontend** | UI/UX work | References DESIGN.md, frontend architecture in CLAUDE.md |
| **Backend** | API or service work | References backend architecture, service patterns, auth model |
| **DevOps** | Infrastructure or deployment | References Makefile, docker-compose, CI pipeline |
| **Security** | Security review | Routes through AGENTS.md patterns, references docs/SECURITY.md |
| **Testing** | Test creation or improvement | References tests/ structure, conftest.py patterns |
| **Release** | Release preparation | Routes through /release, references version system |
| **Ecosystem** | Improving skills, hooks, workflows | Routes through /improve, references governance |
| **Generation** | Creating new commands, hooks, skills | References existing patterns, governance rules |

Ask the user to confirm the classification if ambiguous.

### Step 3: GENERATE

Write the prompt using this structure:

```markdown
# [Objective]

## Context
[What this builds on — reference real files, real state, real phase plan]

## Constraints
[Architecture rules, governance — reference guide.md and CLAUDE.md, don't duplicate them]

## Approach
[How to do it — reference real skills, workflows, hooks that apply]

## Validation
[How to verify — reference real make targets, test commands]

## References
[Links to relevant docs, ADRs, existing patterns in the codebase]
```

**Key rules for generated prompts:**
- Reference real file paths that exist in the repository
- Reference real skills from `.claude/skills/` that apply to this work
- Reference real workflows from `docs/WORKFLOWS.md`
- Reference real governance from `docs/GOVERNANCE.md`
- Do not repeat rules already enforced by hooks (the on-change hook handles lint)
- Do not duplicate architecture constraints — reference `guide.md` instead
- Be concise for simple tasks, detailed for complex ones
- Scale detail to the actual complexity of the work

### Step 4: REVIEW (Self-Audit)

Before presenting the prompt, audit it against these 6 checks:

1. **Clarity:** Would an agent reading this prompt know exactly what to do?
2. **Scoping:** Is the scope defined? Can it be done in one iteration?
3. **Ecosystem leverage:** Does it use existing systems or reinvent them?
4. **Redundancy:** Does it repeat rules already handled by the ecosystem?
5. **Completeness:** Are all integration points mentioned?
6. **Simplicity:** Can it be shorter without losing effectiveness?

### Step 5: REFINE

Fix any issues found in Step 4. Repeat until all 6 checks pass.

### Step 6: PRESENT

Show the final prompt in a code block. After the prompt, offer:

- Edit it based on feedback
- Save it to a file
- Use it immediately (if the user wants to proceed with /cortex or manually)

## Output

```
## Generated Prompt: [topic]

**Category:** [classification]
**Applies to:** [files/systems affected]

[The prompt in a code block]

---
**Ecosystem leverage:**
- Skills: [which skills this prompt uses]
- Workflows: [which workflow stages this follows]
- Hooks: [which hooks will run during execution]
- References: [key docs/files referenced]
```
```

- [ ] **Step 2: Validate file exists and is well-formed**

Run: `cat .claude/commands/project/prompt.md | head -5`
Expected: First line is `# /project:prompt — Ecosystem-Aware Prompt Generator`

Run: `grep -c "Category\|Planning\|Architecture\|Feature\|Bug Fix\|Audit\|Refactor\|Performance\|Frontend\|Backend\|DevOps\|Security\|Testing\|Release\|Ecosystem\|Generation" .claude/commands/project/prompt.md`
Expected: 16+ (all categories present)

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/prompt.md
git commit -m "feat(commands): add /prompt ecosystem-aware prompt generator"
```

---

### Task 3: New Expert Commands — `/audit`, `/verify`, `/release`, `/feature-gap`

**Files:**
- Create: `.claude/commands/project/audit.md`
- Create: `.claude/commands/project/verify.md`
- Create: `.claude/commands/project/release.md`
- Create: `.claude/commands/project/feature-gap.md`

**Interfaces:**
- Consumes: Same ecosystem context (repo state, phase plans, progress, architecture)
- Produces: Structured reports (tables with findings)

**Validation:** All 4 files exist. Each follows Purpose → Instructions → Output structure. Each references real systems. No overlap between `/audit` (code-level) and `/health` (ecosystem-level). No overlap between `/verify` (automated checks) and `/review` (quality analysis). No overlap between `/release` (version completeness) and `/verify` (test results).

- [ ] **Step 1: Create `/audit` command file**

Create `.claude/commands/project/audit.md` with the following content:

```markdown
# /project:audit — Codebase Audit

Deep code-level scan for runtime errors, dead code, integration issues, broken imports, placeholders, and technical debt.

**Scope:** Code-level analysis. For broad ecosystem health (skills, docs, governance trends), use `/project:health` instead.

## Instructions

### 1. Read Scope

```bash
cat ACTIVE_VERSION.md
grep -r "in_progress\|active" .agents/plans/versions/*/progress.md
```

Read the active phase plan to know what components are in scope.

### 2. Baseline

```bash
make check
```

Report: tests pass/fail, lint clean/dirty.

### 3. Runtime Errors

Scan for code that will crash at runtime:

- **Imports:** Find any `ImportError` or missing module references. Run:
  ```bash
  python -c "import backend.app.main" 2>&1
  ```
  Check all service files import their dependencies correctly.

- **Singletons:** Verify all global singletons (llm_manager, redis_cache, download_manager) are properly initialized in their modules.

- **API patterns:** Check all endpoints in `backend/app/api/v1/` for:
  - Missing `response_model=` on decorator
  - Missing ownership checks (`resource.user_id == current_user.id`) on user-scoped endpoints
  - Routes not in correct order (specific before parameterized)

### 4. Dead Code

Find functions, classes, or modules never imported or called:

```bash
# Find potentially unused functions
grep -rn "^def \|^class " backend/app/services/ | head -50
```

For each candidate, apply the **UNIQUE CAPABILITIES TEST:**
- Is it imported anywhere? `grep -rn "from.*import.*FunctionName" backend/`
- If not imported, does it provide a capability not covered by any other service?
- If it provides unique capability: KEEP (not dead code)
- If no unique capability and not imported: flag for deletion

### 5. Integration Issues

- **Service chains:** Verify complete dependency chains:
  - `file_watcher_v2` → `indexing_orchestrator` → `incremental_indexer`/`document_indexer`
  - `deletion_pipeline` handles cascade cleanup
  - `cross_file_search` does graph-enriched search
  - `path_index` provides directory tree browsing

- **Mock patches:** Verify all patches in `tests/conftest.py` match actual service imports:
  ```bash
  grep "patch(" tests/conftest.py
  ```
  For each, verify the import path exists in the actual service file.

- **Model imports:** Verify all models are imported in `migrations/env.py` for Alembic autogenerate.

### 6. Placeholders

Scan for incomplete implementations:

```bash
grep -rn "TODO\|FIXME\|HACK\|XXX\|TBD\|NotImplementedError" backend/ frontend/ --include="*.py" --include="*.ts" --include="*.tsx" | head -30
```

Also scan for:
- `pass` in non-trivial functions (functions longer than just `pass`)
- Mock/placeholder return values in production code (e.g., `return []` in a function that should query a database)

### 7. Consistency

- Cross-reference CLAUDE.md claims vs actual codebase (e.g., if CLAUDE.md says "341 tests", verify)
- Check docs/ references are valid (no broken links to files that don't exist)
- Verify migration chain is unbroken:
  ```bash
  make migrate
  ```

## Output

```markdown
## Audit: [date]

### Baseline
Tests: PASS/FAIL (N/N) | Lint: CLEAN/DIRTY

### Runtime Errors
| # | Severity | File:Line | Issue | Fix |
|---|----------|-----------|-------|-----|

### Dead Code
| # | File:Line | Verdict | Reason |
|---|-----------|---------|--------|

### Integration Issues
| # | Severity | Issue | Fix |
|---|----------|-------|-----|

### Placeholders
| # | File:Line | Type | Content |
|---|-----------|------|---------|

### Consistency
| # | Issue | Fix |
|---|-------|-----|

### Summary
- Runtime errors: N
- Dead code candidates: N (N confirmed dead, N retained for unique capability)
- Integration issues: N
- Placeholders: N
- Consistency gaps: N
```
```

- [ ] **Step 2: Create `/verify` command file**

Create `.claude/commands/project/verify.md` with the following content:

```markdown
# /project:verify — Verification Suite

Run the full verification pipeline and report pass/fail. Fast, focused, no analysis — just automated checks.

**Scope:** Automated pass/fail checks. For code quality analysis and pattern review, use `/project:review` instead.

## Instructions

### 1. Backend Tests

```bash
make test
```

Report: pass/fail, total count, any failures with file:line.

### 2. Frontend Tests

```bash
cd frontend && npm test
```

Report: pass/fail, total count, any failures.

### 3. Lint

```bash
make lint
```

Report: pass/fail, any warnings or errors.

### 4. Format

```bash
make format --check
```

Report: pass/fail, list files needing format if any.

### 5. Build

```bash
cd frontend && npm run build
```

Report: pass/fail, any errors.

### 6. Hooks

```bash
python3 .claude/hooks/run_hooks.py
```

Report: pass/fail per hook.

### 7. Migrations

```bash
make migrate
```

Report: pass/fail, any pending migrations.

## Output

```markdown
## Verification: [date]

| Check | Status | Details |
|-------|--------|---------|
| Backend tests | ✅/❌ N/N | |
| Frontend tests | ✅/❌ N/N | |
| Lint | ✅/❌ | |
| Format | ✅/❌ | [files if failing] |
| Build | ✅/❌ | |
| Hooks | ✅/❌ N/N | |
| Migrations | ✅/❌ | |

### Verdict: PASS / FAIL
```

**Block merge on any FAIL.**
```

- [ ] **Step 3: Create `/release` command file**

Create `.claude/commands/project/release.md` with the following content:

```markdown
# /project:release — Release Readiness Check

Determine if the current state is ready for release of the active version/phase. Combines verification, documentation, governance, and version completeness.

**Scope:** Version/phase release gate. For just test/lint/build results, use `/project:verify` instead.

## Instructions

### 1. Read Version Context

```bash
cat ACTIVE_VERSION.md
cat .agents/plans/versions/vX/progress.md  # (replace X with active version)
```

Read the active phase plan: `.agents/plans/versions/vX/Phase-N.md`

Identify the phase exit criteria.

### 2. Run Verification

Run all `/project:verify` checks:
- Backend tests
- Frontend tests
- Lint
- Format
- Build
- Hooks
- Migrations

Report results.

### 3. Check Phase Completeness

For each exit criterion in the phase plan:
- Is it met? (Yes/No)
- What evidence supports this? (test output, code reference, doc reference)

Flag any incomplete items.

### 4. Check Documentation

| Check | Status |
|-------|--------|
| New/changed APIs in `docs/API.md` | ✅/❌ |
| New models in `docs/DATABASE.md` | ✅/❌ |
| Architecture changes in `docs/ARCHITECTURE.md` | ✅/❌ |
| ADRs created for architectural decisions | ✅/❌ |
| README.md reflects current state | ✅/❌ |

### 5. Check Governance

| Check | Status |
|-------|--------|
| All hooks passing | ✅/❌ |
| `progress.md` up to date | ✅/❌ |
| No unresolved P0/P1 from /review | ✅/❌ |
| No unresolved P0/P1 from /challenge | ✅/❌ |

### 6. Check Git State

| Check | Status |
|-------|--------|
| Clean working tree | ✅/❌ |
| Meaningful commit history | ✅/❌ |
| No merge conflicts | ✅/❌ |

### 7. Check Version Boundaries

- Does anything in this release belong in a different version?
- Is scope creep present? (features from V2+ leaking into V1)

## Output

```markdown
## Release Readiness: [date]

### Version: VX — Phase N: [name]

### Verification
[Results from verify checks]

### Phase Completeness
| Criterion | Status | Evidence |
|-----------|--------|----------|

### Documentation
| Check | Status |
|-------|--------|

### Governance
| Check | Status |
|-------|--------|

### Git State
| Check | Status |
|-------|--------|

### Version Boundaries
| Check | Status |
|-------|--------|

### Verdict: READY / NOT READY
### Blockers: [list if any]
```
```

- [ ] **Step 4: Create `/feature-gap` command file**

Create `.claude/commands/project/feature-gap.md` with the following content:

```markdown
# /project:feature-gap — Roadmap vs Codebase Gap Analysis

Cross-reference roadmap/phase plans against the actual codebase. Find what's planned but not implemented.

**Scope:** Missing/planned work. For issues in existing code, use `/project:audit` instead.

## Instructions

### 1. Read the Roadmap

```bash
cat docs/ROADMAP.md
cat ACTIVE_VERSION.md
cat .agents/plans/versions/vX/progress.md  # (replace X with active version)
```

Read the active phase plan: `.agents/plans/versions/vX/Phase-N.md`

### 2. Scan the Codebase

```bash
# Backend services
ls backend/app/services/

# Backend API endpoints
ls backend/app/api/v1/

# Backend models
ls backend/app/models/

# Frontend features
ls frontend/src/app/
ls frontend/src/components/
```

### 3. Cross-Reference

For each component in the phase plan:

| Check | How |
|-------|-----|
| Service exists? | Does `backend/app/services/<name>.py` exist? |
| Service complete? | Is it more than a stub? Does it have real logic? |
| API endpoint exists? | Is it registered in `backend/app/api/v1/`? |
| Model exists? | Is it in `backend/app/models/`? |
| Migration exists? | Is there a migration for it in `migrations/versions/`? |
| Tests exist? | Is there a test file in `tests/`? |
| Frontend support? | Is there UI for it in `frontend/src/`? |
| Documented? | Is it in the relevant docs/ file? |

### 4. Classify Gaps

For each planned component, classify:

- **Complete** — fully implemented and tested
- **Partial** — started but incomplete
- **Stubbed** — scaffolded but no real implementation
- **Missing** — not started at all

### 5. Estimate Effort

For non-complete components, estimate effort:
- **XS** — a few hours, single file
- **S** — half a day, 1-2 files
- **M** — 1-2 days, 3-5 files
- **L** — 3-5 days, 5-10 files
- **XL** — 1+ weeks, cross-cutting

### 6. Prioritize

Order gaps by:
1. Blocks downstream work (dependency)
2. High impact, low effort (quick wins)
3. High impact, high effort (major features)
4. Low impact (nice-to-haves)

## Output

```markdown
## Feature Gap: [date]

### Version: VX — Phase N: [name]

| Component | Planned | Exists | Status | Tests | Effort |
|-----------|---------|--------|--------|-------|--------|
| [name] | Yes | Yes/No | Complete/Partial/Stubbed/Missing | N/N | XS/S/M/L/XL |

### Summary
- Complete: N components
- Partial: N components
- Stubbed: N components
- Missing: N components
- Total effort: XS/S/M/L/XL

### Recommended Priority
1. [Component] — [reason]
2. [Component] — [reason]

### Quick Wins (high impact, low effort)
- [Component] — [effort estimate]
```
```

- [ ] **Step 5: Validate all 4 files exist**

Run: `ls -la .claude/commands/project/audit.md .claude/commands/project/verify.md .claude/commands/project/release.md .claude/commands/project/feature-gap.md`
Expected: All 4 files exist

Run: `head -1 .claude/commands/project/audit.md .claude/commands/project/verify.md .claude/commands/project/release.md .claude/commands/project/feature-gap.md`
Expected: Each starts with its command title

- [ ] **Step 6: Commit**

```bash
git add .claude/commands/project/audit.md .claude/commands/project/verify.md .claude/commands/project/release.md .claude/commands/project/feature-gap.md
git commit -m "feat(commands): add /audit, /verify, /release, /feature-gap expert commands"
```

---

### Task 4: Refine Existing Commands

**Files:**
- Modify: `.claude/commands/project/architecture.md`
- Modify: `.claude/commands/project/challenge.md`
- Modify: `.claude/commands/project/health.md`
- Modify: `.claude/commands/project/ideas.md`
- Modify: `.claude/commands/project/improve.md`
- Modify: `.claude/commands/project/reflect.md`
- Modify: `.claude/commands/project/review.md`

**Interfaces:**
- Consumes: Same ecosystem context
- Produces: Refined command files with clearer scope and better integration

**Validation:** All 7 files updated. Each change is minimal — additions only, no rewrites. No overlap introduced between commands.

- [ ] **Step 1: Refine `/architecture`**

Read `.claude/commands/project/architecture.md`.

Add the following to the Instructions section, after step 1 ("Read the source of truth"):

```markdown
2. **Check version context.** Read `ACTIVE_VERSION.md`. Verify the proposed change is appropriate for the current version. Changes that belong in a later version should be deferred.
```

Also add to step 3 (Check alignment with CORTEX principles), add this check:

```markdown
- Version alignment: Is this change appropriate for the current version (V1-V6)?
```

Commit:
```bash
git add .claude/commands/project/architecture.md
git commit -m "refactor(commands): add version context check to /architecture"
```

- [ ] **Step 2: Refine `/challenge`**

Read `.claude/commands/project/challenge.md`.

Add a new section after "Wrong Assumptions" (step 2):

```markdown
### Version Boundaries
- Does this change belong in the current version?
- Is this scope creep from a later version?
- Would this be better deferred to a future phase?
```

Commit:
```bash
git add .claude/commands/project/challenge.md
git commit -m "refactor(commands): add version boundary check to /challenge"
```

- [ ] **Step 3: Refine `/health`**

Read `.claude/commands/project/health.md`.

Add a note at the top of the Instructions section:

```markdown
**Scope:** Broad ecosystem health — skills, docs, governance, tech debt trends. For deep code-level scanning (runtime errors, dead code, integration issues), use `/project:audit` instead.
```

Commit:
```bash
git add .claude/commands/project/health.md
git commit -m "refactor(commands): clarify /health scope vs /audit"
```

- [ ] **Step 4: Refine `/ideas`**

Read `.claude/commands/project/ideas.md`.

Add a new step after step 2 ("Read the roadmap"):

```markdown
3. **Check feature gaps.** If a `/project:feature-gap` report exists in `docs/audits/`, read it. Prioritize ideas that address identified gaps.
```

(Renumber subsequent steps.)

Commit:
```bash
git add .claude/commands/project/ideas.md
git commit -m "refactor(commands): add feature-gap cross-reference to /ideas"
```

- [ ] **Step 5: Refine `/improve`**

Read `.claude/commands/project/improve.md`.

Add a new check in the instructions (after "Review governance rules"):

```markdown
6. **Check for generation opportunities.** Based on patterns observed during this review:
   - Should any new command be created? (recurring manual process)
   - Should any new hook be created? (recurring quality issue)
   - Should any new skill be created? (recurring workflow pattern)
   - If yes, recommend with justification.
```

Commit:
```bash
git add .claude/commands/project/improve.md
git commit -m "refactor(commands): add generation opportunity check to /improve"
```

- [ ] **Step 6: Refine `/reflect`**

Read `.claude/commands/project/reflect.md`.

Add a new category to the reflection framework (after "Documentation Gap"):

```markdown
### Ecosystem Growth
- Should any finding become a new skill? (recurring process pattern)
- Should any finding become a new hook? (recurring quality issue)
- Should any finding become a new command? (recurring workflow)
- Should any finding become a new workflow? (multi-step process without automation)
```

Commit:
```bash
git add .claude/commands/project/reflect.md
git commit -m "refactor(commands): add ecosystem growth category to /reflect"
```

- [ ] **Step 7: Refine `/review`**

Read `.claude/commands/project/review.md`.

Add a note at the top of the Instructions section:

```markdown
**Scope:** Code quality — correctness, patterns, completeness. For automated pass/fail checks (tests, lint, build), use `/project:verify` instead.
```

Commit:
```bash
git add .claude/commands/project/review.md
git commit -m "refactor(commands): clarify /review scope vs /verify"
```

---

### Task 5: Quick Guide + Integration Updates

**Files:**
- Create: `.claude/commands/GUIDE.md`
- Modify: `docs/WORKFLOWS.md`
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: All 13 command files (reads their names and purposes)
- Produces: Updated discoverability and integration docs

**Validation:** GUIDE.md exists with all 13 commands. WORKFLOWS.md references new commands. CLAUDE.md commands table includes all 13 commands.

- [ ] **Step 1: Create GUIDE.md**

Create `.claude/commands/GUIDE.md` with the following content:

```markdown
# Command Guide

## Using Commands

Type `/project:<name>` to invoke any command.

## Commands

### Autonomous
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:cortex` | Full development iteration | Start a development session — walks away |

### Prompt Generation
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:prompt` | Generate ecosystem-aware prompts | Before any work, to get a high-quality prompt |

### Expert Commands
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:audit` | Deep code audit | Find bugs, dead code, integration issues |
| `/project:review` | Code quality review | Before push or merge |
| `/project:verify` | Run verification suite | Check tests, lint, build pass |
| `/project:release` | Release readiness | Before releasing a version/phase |
| `/project:architecture` | Architecture alignment | Before big architectural changes |
| `/project:challenge` | Adversarial review | Before major decisions |
| `/project:health` | Repository health | Weekly or before milestones |
| `/project:ideas` | Innovation discovery | Weekly or during planning |
| `/project:improve` | Ecosystem improvement | Weekly or after significant work |
| `/project:reflect` | Reflection framework | Before completing any major task |
| `/project:feature-gap` | Roadmap vs codebase | During planning or phase transitions |

## Typical Workflows

### Quick development session
`/project:cortex` → walks away

### Before a big decision
`/project:challenge` → review findings → decide

### Weekly maintenance
`/project:health` → `/project:ideas` → `/project:improve`

### Before release
`/project:release` → fix blockers → `/project:verify`

### Need a prompt for complex work
`/project:prompt` → review generated prompt → use it

## Priority Order
1. `/project:cortex` — does everything autonomously
2. `/project:prompt` — generates ecosystem-aware prompts
3. Everything else — focused expert tools
```

- [ ] **Step 2: Update WORKFLOWS.md**

Read `docs/WORKFLOWS.md`.

Update Stage 7 (Reflect & Release) to reference the new commands. Find the section that describes the reflect/release stage and add a note:

```markdown
**Command equivalents:**
- Code quality: `/project:review`
- Adversarial: `/project:challenge`
- Reflection: `/project:reflect`
- Verification: `/project:verify`
- Release readiness: `/project:release`
```

Commit:
```bash
git add docs/WORKFLOWS.md
git commit -m "docs: update workflows to reference new command ecosystem"
```

- [ ] **Step 3: Update CLAUDE.md**

Read `CLAUDE.md`.

Find the "Strategic Commands" table. Replace it with the updated command set:

```markdown
## Strategic Commands

| Command | When | Purpose |
|---------|------|---------|
| `/project:cortex` | Start development session | Autonomous development iteration |
| `/project:prompt` | Before complex work | Generate ecosystem-aware prompts |
| `/project:audit` | During audits | Deep code-level scan |
| `/project:review` | Before push | Code quality analysis |
| `/project:verify` | Before merge | Automated verification suite |
| `/project:release` | Before release | Release readiness check |
| `/project:architecture` | Before big changes | Architecture alignment |
| `/project:challenge` | Before decisions | Adversarial review |
| `/project:health` | Weekly | Repository health check |
| `/project:ideas` | Weekly | Innovation discovery |
| `/project:improve` | Weekly | Ecosystem self-improvement |
| `/project:reflect` | Before completion | Reflection framework |
| `/project:feature-gap` | During planning | Roadmap vs codebase gaps |
```

Also update the "Mandatory Reviews" table to reference the correct commands:

```markdown
### Mandatory Reviews

| Review | When | Command |
|--------|------|---------|
| Code quality | Before push | `/project:review` |
| Verification | Before merge | `/project:verify` |
| Adversarial | Before major decisions | `/project:challenge` |
| Reflection | Before completion | `/project:reflect` |
| Architecture | Before big changes | `/project:architecture` |
| Health | Weekly | `/project:health` |
| Release | Before release | `/project:release` |
```

Commit:
```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with new command ecosystem"
```

- [ ] **Step 4: Validate all files**

Run: `ls .claude/commands/project/ | sort`
Expected: All 13 command files present

Run: `ls .claude/commands/GUIDE.md`
Expected: File exists

Run: `grep "/project:" CLAUDE.md | wc -l`
Expected: 13+ (all commands referenced)

- [ ] **Step 5: Final commit**

```bash
git add .claude/commands/GUIDE.md
git commit -m "feat(commands): add command guide for discoverability"
```

---

## Execution Order

| Task | Depends On | Estimated Time |
|------|-----------|---------------|
| Task 1: /cortex | None | 15 min |
| Task 2: /prompt | None | 10 min |
| Task 3: New expert commands | None | 15 min |
| Task 4: Refine existing | None | 10 min |
| Task 5: Guide + integration | Tasks 1-4 (needs all commands to exist) | 10 min |

Tasks 1-4 are independent and can run in parallel. Task 5 depends on all commands being in place.

## Verification

After all tasks:
1. `ls .claude/commands/project/ | wc -l` → 13
2. `ls .claude/commands/GUIDE.md` → exists
3. Every command file starts with `# /project:<name> — <purpose>`
4. Every command has Purpose → Instructions → Output structure
5. No command references another command for invocation
6. All file paths referenced in commands exist in the repo
7. CLAUDE.md and WORKFLOWS.md reference the new commands
