# CORTEX Strategic Command System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 7 slash commands in `.claude/commands/project/` and integrate them into governance docs.

**Architecture:** Each command is a `.md` file in `.claude/commands/project/` that Claude Code exposes as `/project:<name>`. Commands contain structured prompts that run analysis when invoked. Governance docs updated to reference commands in workflows.

**Tech Stack:** Claude Code slash commands (Markdown files), CLAUDE.md governance, docs updates.

## Global Constraints

- All commands live in `.claude/commands/project/`
- Command files are Markdown with structured prompts (not executable code)
- Each command produces terminal output; significant findings save to `docs/audits/` or `docs/ideas/`
- `/project:reflect` is mandatory (CLAUDE.md rule); others are on-demand
- No command duplicates an existing hook's functionality
- All changes committed on feature branch, merged to main after verification

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `.claude/commands/project/reflect.md` | Create | Reflection framework command |
| `.claude/commands/project/review.md` | Create | Code quality review command |
| `.claude/commands/project/challenge.md` | Create | Adversarial review command |
| `.claude/commands/project/health.md` | Create | Repository health check command |
| `.claude/commands/project/architecture.md` | Create | Architecture alignment command |
| `.claude/commands/project/ideas.md` | Create | Innovation discovery command |
| `.claude/commands/project/improve.md` | Create | Ecosystem improvement command |
| `CLAUDE.md:197-198` | Modify | Add Reflection Rule section after Mandatory Workflow Rules |
| `CLAUDE.md:222-223` | Modify | Add Strategic Commands reference section |
| `docs/GOVERNANCE.md:204` | Modify | Add `/project:review` to Mandatory Before Every PR |
| `docs/WORKFLOWS.md:89-94` | Modify | Add `/project:review` and `/project:challenge` to Stage 4 |
| `docs/WORKFLOWS.md:102-107` | Modify | Add `/project:reflect` to Stage 5 |

---

### Task 1: Create `/project:reflect` Command

**Files:**
- Create: `.claude/commands/project/reflect.md`

**Interfaces:**
- Consumes: Current work context (files changed, features built)
- Produces: Structured reflection findings in terminal; saves to `docs/audits/YYYY-MM-DD-reflect.md` if action-items exist

- [ ] **Step 1: Create the commands directory**

```bash
mkdir -p .claude/commands/project
```

- [ ] **Step 2: Write the reflect command**

Create `.claude/commands/project/reflect.md` with this content:

```markdown
# /project:reflect — Reflection Framework

Before completing any major task, run through this reflection framework systematically.

## Instructions

1. **Identify the work just completed.** Run `git diff --stat HEAD~1` to see what changed. Summarize: files modified, features built, bugs fixed.

2. **Run through the reflection framework.** For each question, analyze the actual code and changes — don't just answer abstractly.

### Quality
- Could any code be cleaner, simpler, more readable?
- Are there functions that do too much?
- Are variable/function names clear and descriptive?
- Is error handling comprehensive?

### Redundancy
- Is anything duplicated that could be consolidated?
- Are there similar patterns in different files that could share a utility?
- Are there repeated strings/values that should be constants?

### Automation
- Is any manual step that could be automated?
- Are there repetitive commands the developer runs that could be a Make target?
- Are there manual checks that could become hooks?

### Skill Opportunity
- Could this workflow become a reusable skill?
- Is this a Cortex-specific process that agents should follow consistently?
- Would a skill prevent mistakes in future executions?

### Hook Opportunity
- Should any validation here become a hook?
- Is there a check that should run automatically on every commit/push?
- Would a hook catch this class of issue earlier?

### Workflow Opportunity
- Does this reveal a new or improved workflow?
- Is there a gap in the current workflow definitions?
- Should docs/WORKFLOWS.md be updated?

### Future Problem
- What downstream issues might this create?
- Does this introduce technical debt?
- Will this scale poorly as the codebase grows?

### Future Opportunity
- What doors does this open?
- Could this capability be extended or composed with other features?
- Does this enable new use cases?

### Documentation Gap
- Is anything undocumented that should be?
- Are there new APIs, patterns, or decisions that need documenting?
- Should docs/ARCHITECTURE.md or other docs be updated?

### Test Gap
- Is any behavior untested that should be?
- Are edge cases covered?
- Would integration tests catch issues unit tests miss?

3. **Assign severity** to each finding:
- **insight** — observation, no action needed
- **suggestion** — worth considering, not urgent
- **action-item** — should be done, create a task or issue

4. **Output** structured findings in terminal with this format:

```
## Reflection: [date]

### Findings
| # | Category | Severity | Finding | Recommendation |
|---|----------|----------|---------|----------------|
| 1 | quality | action-item | ... | ... |

### Summary
- Insights: N
- Suggestions: N
- Action items: N
```

5. If action-items exist, save report to `docs/audits/YYYY-MM-DD-reflect.md`.

6. If skill/hook/workflow creation opportunities found, list them explicitly for follow-up.
```

- [ ] **Step 3: Verify the command file is valid**

Run: `ls -la .claude/commands/project/reflect.md`
Expected: file exists with content

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/project/reflect.md
git commit -m "feat: add /project:reflect command"
```

---

### Task 2: Create `/project:review` Command

**Files:**
- Create: `.claude/commands/project/review.md`

**Interfaces:**
- Consumes: Git diff of changed files, AGENTS.md patterns
- Produces: Pass/fail review output with file:line references

- [ ] **Step 1: Write the review command**

Create `.claude/commands/project/review.md` with this content:

```markdown
# /project:review — Code Quality Review

Run this before pushing code or creating a PR. Reviews changed code for correctness, patterns, and completeness.

## Instructions

1. **Identify changed files.** Run `git diff --name-only HEAD~1` and `git diff HEAD~1` to see all changes.

2. **Run linting and tests.**
- Run: `make lint`
- Run: `make test`
- Report pass/fail for each.

3. **Review each changed file** for:

### Correctness
- Missing error handling (bare `except:`, swallowed exceptions)
- Off-by-one errors, null checks, type mismatches
- Race conditions, resource leaks

### API Patterns
- Missing `response_model=` on API endpoint decorators
- Missing ownership checks (`resource.user_id == current_user.id`) on user-scoped endpoints
- Routes not in correct order (specific before parameterized)
- Missing router registration in `api/router.py`

### Code Quality
- Hardcoded values that should be in config
- Missing docstrings on public functions
- Overly complex logic that could be simplified
- Dead code or unused imports

### Testing
- New functions/classes without tests
- Edge cases not covered
- Missing integration tests for API endpoints

### Documentation
- New/changed APIs not reflected in docs/API.md
- New models not reflected in docs/DATABASE.md
- Architecture changes not reflected in docs/ARCHITECTURE.md

4. **Output** format:

```
## Code Review: [date]

### Lint: PASS/FAIL
### Tests: PASS/FAIL

### Findings
| # | Severity | File:Line | Issue | Fix |
|---|----------|-----------|-------|-----|
| 1 | P0 | path/to/file.py:42 | ... | ... |

### Summary
- P0 (critical): N
- P1 (important): N
- P2 (minor): N
- Clean: N files
```

5. **Block push** if any P0 findings exist. P1/P2 are advisory.
```

- [ ] **Step 2: Verify the command file exists**

Run: `ls -la .claude/commands/project/review.md`
Expected: file exists

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/review.md
git commit -m "feat: add /project:review command"
```

---

### Task 3: Create `/project:challenge` Command

**Files:**
- Create: `.claude/commands/project/challenge.md`

**Interfaces:**
- Consumes: Current plan/spec/design, CORTEX principles from docs/ARCHITECTURE.md
- Produces: Numbered list of challenges with severity

- [ ] **Step 1: Write the challenge command**

Create `.claude/commands/project/challenge.md` with this content:

```markdown
# /project:challenge — Adversarial Review

Run this before implementing a significant feature or making an architectural choice. Actively tries to poke holes in the current approach.

## Instructions

1. **Read the current plan/spec/design.** Check for:
- `docs/superpowers/specs/` — latest design spec
- `docs/superpowers/plans/` — latest implementation plan
- Recent git commits — what's being worked on

2. **Challenge the approach.** For each challenge, be specific — reference actual code, actual dependencies, actual constraints.

### Risks & Failure Modes
- What could go wrong?
- What are the single points of failure?
- What happens under load/error conditions?

### Edge Cases
- What boundary conditions aren't handled?
- What happens with empty inputs, large inputs, concurrent access?
- What happens when external services are unavailable?

### Over/Under-Engineering
- Is this more complex than it needs to be?
- Is this too simple for the actual requirements?
- Are there simpler approaches that achieve the same goal?

### Wrong Assumptions
- What assumptions might be incorrect?
- What data contradicts these assumptions?
- What would invalidate this approach?

### Unexplored Alternatives
- What other approaches were considered?
- What would a different architecture look like?
- What do similar projects do?

3. **Verify alignment with CORTEX principles:**
- **Privacy-first:** Does this introduce any external data leaks?
- **Compound learning:** Does this contribute to or hinder knowledge accumulation?
- **Two-tier trust:** Does this respect the account/vault separation?
- **Graceful degradation:** Does this work when optional services are unavailable?
- **Model freedom:** Does this lock into a specific model/provider?
- **Living knowledge:** Does this connect to or fragment the knowledge graph?

4. **Output** format:

```
## Challenge: [date]

### Approach Being Challenged
[Brief description]

### Challenges
| # | Severity | Category | Challenge | Alternative |
|---|----------|----------|-----------|-------------|
| 1 | critical | risk | ... | ... |

### CORTEX Principle Alignment
| Principle | Status | Notes |
|-----------|--------|-------|
| Privacy-first | ✅/⚠️/❌ | ... |

### Summary
- Critical: N
- Warning: N
- Nit: N
```

5. Challenges are advisory — they inform the decision, they don't block it.
```

- [ ] **Step 2: Verify the command file exists**

Run: `ls -la .claude/commands/project/challenge.md`
Expected: file exists

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/challenge.md
git commit -m "feat: add /project:challenge command"
```

---

### Task 4: Create `/project:health` Command

**Files:**
- Create: `.claude/commands/project/health.md`

**Interfaces:**
- Consumes: All hooks (`.claude/hooks/run_hooks.py`), automation scripts (`scripts/automation/`), skill inventory (`.claude/skills/`)
- Produces: Health report in terminal; saves to `docs/audits/YYYY-MM-DD-health-report.md`

- [ ] **Step 1: Write the health command**

Create `.claude/commands/project/health.md` with this content:

```markdown
# /project:health — Repository Health Check

Run weekly or before major milestones. Comprehensive health check across all systems.

## Instructions

1. **Run all hooks.**
```bash
python3 .claude/hooks/run_hooks.py
```
Report: pass/fail per hook, findings.

2. **Run automation health checks.**
```bash
python3 scripts/automation/run_all.py health
```
Report: dead code, duplicates, dependencies, drift.

3. **Run bug discovery.**
```bash
python3 scripts/automation/run_all.py bug-discovery
```
Report: placeholders, security issues, error patterns.

4. **Check skill health.**
- List all skills in `.claude/skills/`
- For each, check if it has a definition file (`.md`, `.txt`, `.yaml`, `.py`)
- Check last modification date — flag skills not updated in 30+ days as stale
- List any skills that appear unused (no references in docs or workflows)

5. **Check documentation freshness.**
- For each doc in `docs/`, check if it has a "Last updated" date
- Flag docs that reference outdated information (old phase numbers, stale links)
- Check for broken cross-references between docs

6. **Check tech debt hotspots.**
```bash
git log --oneline --since="2 weeks ago" | head -50
```
- Identify files changed 5+ times in recent commits
- Count TODO/FIXME/HACK/XXX/TBD comments in codebase
- List files with the most technical debt indicators

7. **Output** format:

```
## Health Report: [date]

### Hooks: X/11 passed
[Per-hook results]

### Automation Health
[Per-phase results]

### Bug Discovery
[Per-category results]

### Skill Health
- Total: N
- Complete: N
- Stale: N
- Unused: N

### Documentation
- Total: N
- With dates: N
- Outdated: N
- Broken links: N

### Tech Debt
- Hotspot files: N
- TODO/FIXME count: N
- Recommendations: N

### Health Score: X/100
```

8. Save report to `docs/audits/YYYY-MM-DD-health-report.md`.
```

- [ ] **Step 2: Verify the command file exists**

Run: `ls -la .claude/commands/project/health.md`
Expected: file exists

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/health.md
git commit -m "feat: add /project:health command"
```

---

### Task 5: Create `/project:architecture` Command

**Files:**
- Create: `.claude/commands/project/architecture.md`

**Interfaces:**
- Consumes: `docs/ARCHITECTURE.md`, `docs/decisions/` (ADRs), proposed change description
- Produces: Alignment report with pass/warn/fail per check

- [ ] **Step 1: Write the architecture command**

Create `.claude/commands/project/architecture.md` with this content:

```markdown
# /project:architecture — Architecture Alignment Check

Run before implementing significant new systems or modifying core architecture.

## Instructions

1. **Read the source of truth.** Read `docs/ARCHITECTURE.md` completely.

2. **Understand the proposed change.** Check:
- Recent git commits (`git log --oneline -10`)
- Active plan files (`docs/superpowers/plans/`)
- Active spec files (`docs/superpowers/specs/`)
- The user's stated goal in the current conversation

3. **Check alignment with documented architecture:**
- Does the change fit within the documented system structure?
- Does it follow the existing service layer pattern?
- Does it use the correct database conventions (SQLAlchemy + Alembic)?
- Does it follow the auth model (JWT + cookies, ownership checks)?

4. **Check alignment with CORTEX principles:**
- Privacy-first: No external data leaks introduced?
- Compound learning: Contributes to knowledge accumulation?
- Two-tier trust: Respects account/vault separation?
- Graceful degradation: Works without optional services?
- Model freedom: Not locked to specific provider?
- Living knowledge: Connects to knowledge graph?

5. **Check file placement:**
- Models → `backend/app/models/`
- Schemas → `backend/app/schemas/`
- Routers → `backend/app/api/v1/`
- Services → `backend/app/services/`
- Managers → `backend/app/managers/`
- Middleware → `backend/app/middleware/`
- Tasks → `backend/app/tasks/`
- Tests → `tests/`
- Migrations → `migrations/versions/`
- Docs → `docs/`
- ADRs → `docs/decisions/`

6. **Check for architecture drift:**
- Are there any competing doc systems?
- Are there any duplicate skill directories?
- Are there files in the wrong location?
- Are there unused or stale files?

7. **Check if ADR is needed.** An ADR is required when:
- New technology is introduced
- Architecture pattern changes
- Security policy changes
- API design decisions
- Database schema philosophy changes
- Testing strategy changes
- Deployment approach changes

Check `docs/decisions/` for existing ADRs. If the change qualifies and no ADR exists, recommend creating one.

8. **Output** format:

```
## Architecture Alignment: [date]

### Proposed Change
[Brief description]

### Architecture Fit: PASS/WARN/FAIL
| Check | Status | Notes |
|-------|--------|-------|
| Fits documented architecture | ✅/⚠️/❌ | ... |
| Follows service layer pattern | ✅/⚠️/❌ | ... |
| Correct DB conventions | ✅/⚠️/❌ | ... |
| Auth model respected | ✅/⚠️/❌ | ... |

### CORTEX Principles: PASS/WARN/FAIL
| Principle | Status | Notes |
|-----------|--------|-------|
| Privacy-first | ✅/⚠️/❌ | ... |

### File Placement: PASS/WARN/FAIL
[Files that are in wrong locations]

### Architecture Drift: PASS/WARN/FAIL
[Drift findings]

### ADR Required: YES/NO
[If yes, recommend title and key decisions]

### Summary
- Overall: PASS/WARN/FAIL
- Issues: N
- Recommendations: N
```
```

- [ ] **Step 2: Verify the command file exists**

Run: `ls -la .claude/commands/project/architecture.md`
Expected: file exists

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/architecture.md
git commit -m "feat: add /project:architecture command"
```

---

### Task 6: Create `/project:ideas` Command

**Files:**
- Create: `.claude/commands/project/ideas.md`

**Interfaces:**
- Consumes: Recent commits, `docs/ROADMAP.md`, README.md vision, `docs/ARCHITECTURE.md`
- Produces: Prioritized idea list; saves to `docs/ideas/YYYY-MM-DD.md` if 3+ ideas

- [ ] **Step 1: Write the ideas command**

Create `.claude/commands/project/ideas.md` with this content:

```markdown
# /project:ideas — Innovation & Opportunity Discovery

Run weekly or monthly during planning/strategy sessions. Discovers new features, improvements, and strategic opportunities.

## Instructions

1. **Analyze recent progress.**
```bash
git log --oneline --since="2 weeks ago"
```
What was built? What patterns emerge? What's accelerating?

2. **Read the roadmap.** Read `docs/ROADMAP.md`. What's next? What's partially complete? What's blocked?

3. **Read the vision.** Read the Vision section of `README.md`. What's the gap between current state and the vision?

4. **Identify opportunities** in each category:

### Feature Opportunities
- What new features would advance the CORTEX vision?
- What existing features could be extended?
- What would users find most valuable?

### Improvement Opportunities
- What existing features are incomplete or rough?
- What UX patterns could be improved?
- What performance bottlenecks exist?

### Competitive Opportunities
- What do similar projects (Open Interpreter, Aider, Continue, etc.) do well?
- What gaps exist in the market that CORTEX could fill?
- What unique advantages does CORTEX have (local-first, privacy, knowledge graph)?

### Capability Opportunities
- What new use cases could existing capabilities serve?
- Could features be composed in new ways?
- What integrations would add value?

### Ecosystem Opportunities
- What new skills could be created?
- What new hooks would improve quality?
- What workflows could be automated?

5. **Prioritize** each idea:
- **P0** — critical for vision, do soon
- **P1** — important, plan for next phase
- **P2** — valuable, Backlog
- **P3** — interesting, future consideration

6. **Output** format:

```
## Ideas: [date]

### Progress Analysis
[What was accomplished recently]

### Vision Gap
[What's missing between current state and vision]

### Ideas
| # | Priority | Category | Idea | Effort | Impact |
|---|----------|----------|------|--------|--------|
| 1 | P0 | feature | ... | M | High |

### Summary
- Total ideas: N
- P0: N, P1: N, P2: N, P3: N
- Top recommendation: ...
```

7. If 3+ ideas found, save to `docs/ideas/YYYY-MM-DD.md`.
```

- [ ] **Step 2: Verify the command file exists**

Run: `ls -la .claude/commands/project/ideas.md`
Expected: file exists

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/ideas.md
git commit -m "feat: add /project:ideas command"
```

---

### Task 7: Create `/project:improve` Command

**Files:**
- Create: `.claude/commands/project/improve.md`

**Interfaces:**
- Consumes: Skill inventory, hooks, workflows, governance docs, recent commits
- Produces: Improvement recommendations; saves to `docs/audits/YYYY-MM-DD-improve.md` if action-items exist

- [ ] **Step 1: Write the improve command**

Create `.claude/commands/project/improve.md` with this content:

```markdown
# /project:improve — Ecosystem Self-Improvement

Run weekly or after completing significant work. Reviews and enhances skills, hooks, workflows, and governance.

## Instructions

1. **Review skill usage.**
- Check git log for recent skill invocations
- Which skills from `.claude/skills/` were used?
- Which were skipped? Why?
- Were there skill creation opportunities that weren't acted on?
- Are any skills stale (not updated in 30+ days)?

2. **Review hook effectiveness.**
- Run `python3 .claude/hooks/run_hooks.py` — any false positives?
- Are there checks that should be hooks but aren't?
- Are any hooks producing noisy/irrelevant findings?
- Is the hook phase configuration optimal?

3. **Review workflow gaps.**
- Read `docs/WORKFLOWS.md`
- Are there manual steps that could be automated?
- Are any workflows unclear or incomplete?
- Do workflows match actual development practices?
- Are there missing workflows for common tasks?

4. **Review documentation.**
- Check all docs in `docs/` for completeness
- Are cross-references valid?
- Are there topics not covered by any doc?
- Is the developer guide up to date?

5. **Review governance rules.**
- Read `docs/GOVERNANCE.md`
- Are there rules that need updating?
- Are there new patterns that should be codified?
- Are clarification rules still appropriate?

6. **Generate improvement recommendations.** For each:
- What: specific improvement
- Why: what problem it solves
- Effort: S/M/L
- Priority: now / soon / later

7. **Output** format:

```
## Ecosystem Improvement: [date]

### Skill Review
- Used: N
- Stale: N
- Creation opportunities: N

### Hook Review
- False positives: N
- Missing hooks: N
- Recommendations: N

### Workflow Review
- Gaps found: N
- Recommendations: N

### Documentation Review
- Outdated: N
- Missing topics: N
- Recommendations: N

### Governance Review
- Updates needed: N
- Recommendations: N

### Improvement Recommendations
| # | Priority | Category | What | Why | Effort |
|---|----------|----------|------|-----|--------|
| 1 | now | skill | ... | ... | S |

### Summary
- Total recommendations: N
- Now: N, Soon: N, Later: N
```

8. If action-items found, save to `docs/audits/YYYY-MM-DD-improve.md`.
```

- [ ] **Step 2: Verify the command file exists**

Run: `ls -la .claude/commands/project/improve.md`
Expected: file exists

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/project/improve.md
git commit -m "feat: add /project:improve command"
```

---

### Task 8: Integrate Commands into CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (lines 197-198 and 222-223)

**Interfaces:**
- Consumes: 7 command definitions from Tasks 1-7
- Produces: Updated CLAUDE.md with Reflection Rule and Strategic Commands sections

- [ ] **Step 1: Add Reflection Rule to CLAUDE.md**

After line 197 (end of Mandatory Workflow Rules, after rule 12), insert:

```markdown

### Reflection Rule

Before completing any major task, agents MUST run through the reflection framework. Ask:

- What could be improved?
- What could be simplified?
- What could be automated?
- What could become a skill?
- What could become a hook?
- What could become a reusable workflow?
- What future problem does this reveal?
- What future opportunity does this create?

Use `/project:reflect` for structured execution. Document findings. Never skip reflection.
```

- [ ] **Step 2: Add Strategic Commands section to CLAUDE.md**

After line 222 (after the governance/workflow cross-references, before `## Agent Skills`), insert:

```markdown

## Strategic Commands

| Command | When | Purpose |
|---------|------|---------|
| `/project:reflect` | Before completion (mandatory) | Reflection framework — quality, improvement, ecosystem growth |
| `/project:review` | Before PR/push | Code quality, correctness, patterns |
| `/project:challenge` | Before major decisions | Adversarial review — poke holes in approach |
| `/project:health` | Weekly | Repo health, dead code, drift, debt |
| `/project:architecture` | Before big changes | Architecture alignment, convention check |
| `/project:ideas` | Weekly/monthly | Innovation, future opportunities, gap discovery |
| `/project:improve` | Weekly | Ecosystem improvement — skills, hooks, workflows |

```

- [ ] **Step 3: Verify CLAUDE.md is valid**

Run: `wc -l CLAUDE.md`
Expected: ~260 lines (was ~237, added ~23 lines)

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add reflection rule and strategic commands to CLAUDE.md"
```

---

### Task 9: Integrate Commands into Governance & Workflows

**Files:**
- Modify: `docs/GOVERNANCE.md:204` (add `/project:review` to Mandatory Before Every PR)
- Modify: `docs/WORKFLOWS.md:89-94` (update Stage 4)
- Modify: `docs/WORKFLOWS.md:102-107` (update Stage 5)

**Interfaces:**
- Consumes: Command definitions from Tasks 1-7
- Produces: Updated governance and workflow docs

- [ ] **Step 1: Add /project:review to GOVERNANCE.md**

In `docs/GOVERNANCE.md`, after line 204 (item 5 in "Mandatory Before Every PR"), add:

```markdown
6. Run `/project:review` for code quality analysis
```

- [ ] **Step 2: Update Stage 4 in WORKFLOWS.md**

In `docs/WORKFLOWS.md`, replace lines 89-94 (Stage 4 steps) with:

```markdown
**Steps:**
1. Agent runs `/project:review` for code quality analysis
2. Agent runs `/project:challenge` for adversarial review (if architectural decision)
3. Agent runs code-review skill for correctness
4. Agent runs simplify skill for quality
5. Agent verifies each finding independently
6. Agent addresses P0/P1 findings
7. Agent presents review results to human
```

- [ ] **Step 3: Update Stage 5 in WORKFLOWS.md**

In `docs/WORKFLOWS.md`, replace lines 102-107 (Stage 5 steps) with:

```markdown
**Steps:**
1. Agent runs `/project:reflect` for reflection framework
2. Agent runs full `make check` + `npm run build`
3. Agent updates changelog if user-facing change
4. Agent creates PR with clear description
5. Human reviews and approves
6. Agent merges
```

- [ ] **Step 4: Update lifecycle diagram in WORKFLOWS.md**

In `docs/WORKFLOWS.md`, update the stages diagram (line 12) to:

```
Idea → Branch → Skill Discovery → Triage → Plan → Build → Review → Reflect → Release
```

- [ ] **Step 5: Verify docs are consistent**

Run: `grep -n "project:" CLAUDE.md docs/GOVERNANCE.md docs/WORKFLOWS.md`
Expected: references in all three files

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md docs/GOVERNANCE.md docs/WORKFLOWS.md
git commit -m "docs: integrate strategic commands into governance and workflows"
```

---

### Task 10: Update .gitignore and Final Verification

**Files:**
- Modify: `.gitignore` (add `docs/ideas/` generated file patterns if needed)
- Verify: All 7 command files exist and are well-formed

**Interfaces:**
- Consumes: All files created in Tasks 1-9
- Produces: Clean, verified implementation

- [ ] **Step 1: Verify all 7 commands exist**

```bash
ls -la .claude/commands/project/
```
Expected: 7 files (reflect.md, review.md, challenge.md, health.md, architecture.md, ideas.md, improve.md)

- [ ] **Step 2: Verify CLAUDE.md has both new sections**

```bash
grep -n "Reflection Rule\|Strategic Commands" CLAUDE.md
```
Expected: two matches with line numbers

- [ ] **Step 3: Verify GOVERNANCE.md has /project:review**

```bash
grep -n "project:review" docs/GOVERNANCE.md
```
Expected: one match

- [ ] **Step 4: Verify WORKFLOWS.md has command references**

```bash
grep -n "project:" docs/WORKFLOWS.md
```
Expected: matches for reflect, review, challenge

- [ ] **Step 5: Verify no broken cross-references**

```bash
grep -n "project:" CLAUDE.md docs/GOVERNANCE.md docs/WORKFLOWS.md docs/DEVELOPER_GUIDE.md
```
Expected: references across governance docs

- [ ] **Step 6: Final commit if any cleanup needed**

```bash
git add -A
git commit -m "chore: final verification and cleanup for strategic command system"
```

---

### Task 11: Merge to Main

**Files:** None (git operations only)

**Interfaces:**
- Consumes: All commits from Tasks 1-10 on feature branch
- Produces: Clean main branch with all changes

- [ ] **Step 1: Run full verification on feature branch**

```bash
python3 .claude/hooks/run_hooks.py docs-consistency
```
Expected: PASS (no broken links in new docs)

- [ ] **Step 2: Merge to main**

```bash
git checkout main
git merge feat/strategic-command-system --no-ff -m "feat: implement CORTEX strategic command system"
```

- [ ] **Step 3: Verify main is clean**

```bash
git status
git log --oneline -5
```
Expected: clean working tree, merge commit visible

- [ ] **Step 4: Delete feature branch**

```bash
git branch -d feat/strategic-command-system
```
