# /project:enhance_plan — Planning Ecosystem Improver

**NOT** an implementation command. An **ecosystem intelligence** command. It reviews the entire planning ecosystem and actively improves it — filling gaps between current implementation, future vision, roadmap, architecture, and documentation.

## When to Run

After completing a significant phase or version, or when planning work reveals inconsistencies in the roadmap or plans. Do **not** run during active implementation.

## Philosophy

This command does **four** separate things:

| Dimension | What It Detects | What It Improves |
|-----------|----------------|------------------|
| **Implementation drift** | Code exists but plan says not started | Update progress, close milestones |
| **Planning drift** | Plan says done but code is missing | Find gaps, add to backlog |
| **Architecture drift** | Implementation diverged from documented design | Update ADRs, guide.md |
| **Vision drift** | Roadmap no longer reflects actual direction | Flag for user, never change automatically |

Never change product vision automatically. Flag vision drift for user decision.

## Instructions

### Step 0: Load the Planning Ecosystem

Run:

```bash
# Current git state
git status
git branch --show-current
git log --oneline -5

# Active version
cat .agents/plans/ACTIVE_VERSION.md

# Progress
cat .agents/plans/versions/v*/progress.md 2>/dev/null | grep -E "^\| Phase |^\| \*\*V" || true
grep -r "in_progress\|active\|complete" .agents/plans/versions/*/progress.md 2>/dev/null || true

# Test counts — ground truth
make test --dry-run 2>/dev/null || true
pytest --collect-only 2>&1 | tail -3 || true
```

Read all of:

- `.agents/plans/guide.md` — the constitution
- `.agents/plans/implementation_steps.md` — execution order
- `.agents/plans/FinalCompatibilities.md` — version cross-reference
- `docs/ROADMAP.md` — the roadmap
- Active version plan (e.g. `versions/v1/Phase-2.md`)
- Active version progress (e.g. `versions/v1/progress.md`)

Have a working understanding of:

- `.claude/commands/project/` — all commands
- `.agents/skills/INDEX.md` (if exists) — available skills
- `docs/WORKFLOWS.md` — development workflow
- `docs/GOVERNANCE.md` — governance rules
- Relevant ADRs from `docs/decisions/`

**Outcome:** Complete understanding of the planned state vs actual state.

---

### Step 1: Scan for Implementation Drift

Compare what the phase plans say should exist against what actually exists.

For each component in every active and upcoming phase plan, check:

| Check | How |
|-------|-----|
| Service exists? | `ls backend/app/services/<name>.py` |
| Model exists? | `ls backend/app/models/<name>.py` |
| Router exists? | `ls backend/app/api/v1/<name>.py` |
| Module exists? | `ls path/in/plan` |
| Tests exist? | `ls tests/test_<name>.py` or `ls tests/agents/test_<name>.py` |

Also check for reverse drift: **completed code that the plan hasn't acknowledged**.

| Check | How |
|-------|-----|
| Module exists but plan says not started? | Grep progress.md for "not started" and verify against filesystem |
| Tests pass count higher than plan claims? | Run `pytest --collect-only 2>&1 \| tail -1` |
| Feature complete but progress unmarked? | Check recent git log for feature commits |

**Outcome:** Map of what's actually implemented vs what the plans claim.

---

### Step 2: Scan for Planning Drift

Compare plans against each other for consistency.

Check:

1. **ROADMAP.md vs phase plans** — Do phase names, statuses, and version descriptions match the actual plan documents? ROADMAP.md is the public face — it must match reality.

2. **ACTIVE_VERSION.md vs progress.md** — Does the active version/phase in ACTIVE_VERSION.md match the status in progress.md?

3. **implementation_steps.md vs phase plans** — Do the deliverables listed in implementation_steps.md match each Phase-N.md?

4. **FinalCompatibilities.md vs phase plans** — Does the ODYSSEUS cross-reference still reflect the actual phase plan content?

5. **Phase plans across versions** — Are there any contradictions between V1 Phase-2 requirements and V2 Phase-1 dependencies? (e.g., V1 plan saying "add Provider Protocol" but V2 Phase-1 listing it as a new item)

6. **Version transition criteria** — Is it documented what "Version N complete" actually means? Is there a checklist?

7. **Exit criteria currency** — Do exit criteria in phase plans still match the actual deliverables? Remove stale criteria, add missing ones.

**Outcome:** Map of planning inconsistencies and contradictions.

---

### Step 3: Scan for Architecture Drift

Compare the declared architecture in `guide.md` and ADRs against the actual codebase.

For each architecture section in `guide.md` §4 (Daemon, Desktop, Memory, Graph, Retrieval, Agent, Workflow, Plugin, CLI, Ecosystem):

- Is the "current approach" description accurate?
- Is the "final decision" still the intended direction?
- Has any implementation diverged from the documented design?

Also check ADRs in `docs/decisions/`:

- Read the README at `docs/decisions/README.md` for ordering
- For each ADR, verify its decision is still reflected in the codebase
- Mark any ADRs that have been superseded
- Identify any undocumented decisions that need an ADR

**Outcome:** Map of architecture drift and ADR coverage gaps.

---

### Step 4: Classify and Prioritize Findings

Present all findings organized by improvement type.

Use these categories, **separated**:

```
## Implementation Improvements
Things to build or update in code. Contribute to actual deliverables. Update plans to match reality.

## Planning Improvements
Things to update in plans. No code changes. Only documentation of plans, progress, and roadmap.

## Architecture Improvements
Things to update in architecture docs or ADRs. No code changes. Only documentation of design intent.

## Vision Improvements
**Flagged for user decision.** Never change automatically.
```

For each finding, assign severity:

| Severity | Meaning | Action |
|----------|---------|--------|
| **action-item** | Blocks clarity or execution | Fix in this session |
| **suggestion** | Would improve quality | Fix or document for backlog |
| **insight** | Observation, no action needed | Record only |

---

### Step 5: Brainstorm Improvements

Before making any changes, brainstorm:

1. **Can execution order be improved?** Are there dependencies in the plans that no longer exist? Could something be parallelized?

2. **Can developer experience be improved?** Is there friction in how plans are structured? Missing information? Unclear handoffs?

3. **Are there missing milestones?** Phases that need sub-milestones? Versions missing phase definitions?

4. **Are there documentation gaps?** Plans missing rationale? ADR missing key trade-offs? ROADMAP overview missing?

5. **Are there feature gaps from cross-references?** Items from FinalCompatibilities.md not yet added to any phase plan?

Use the brainstorming approach: for each potential improvement, ask:
- What problem does it solve?
- Is the improvement worth the documentation overhead?
- Does it align with the constitution (guide.md)?

Document which improvements are applied and which are deferred.

**Do not** generate a `/project:prompt` full artifact. Brainstorm internally and document the conclusions.

---

### Step 6: Apply Improvements

For each action-item finding, apply the fix.

Rules:

- **Never change product vision.** Flag vision drift for user. Flag and stop.
- **Update plans to match code, not the reverse.** Plans document intent — when code diverges from intent, update the plan or document an ADR.
- **Keep progress.md accurate.** If code exists, mark its component complete. If a component was renamed, update the component name.
- **Keep ROADMAP.md accurate.** If phase names changed, update them. If version scope shifted, reflect it.
- **Update test counts** wherever they appear (implementation_steps.md, ROADMAP.md, features.md) to match the actual `pytest --collect-only` output.
- **Update ACTIVE_VERSION.md** if the active phase has changed.
- **Create ADRs for undocumented decisions.** If a significant architectural choice was made without an ADR, create one.

For each applied improvement, document:
- What changed
- Why
- Which planning artifact was modified

**Outcome:** All action-items resolved. Planning ecosystem reflects reality.

---

### Step 7: Produce Enhancement Report

```text
## Planning Enhancement: YYYY-MM-DD

### Summary
- Implementation drift items: N
- Planning drift items: N
- Architecture drift items: N
- Vision drift items: N (flagged for user)
- Applied improvements: N
- Deferred improvements: N

### Implementation Improvements Applied
| Plan | Change | Rationale |
|------|--------|-----------|
| progress.md | ... | ... |

### Planning Improvements Applied
| Document | Change | Rationale |
|----------|--------|-----------|
| ROADMAP.md | ... | ... |
| ACTIVE_VERSION.md | ... | ... |

### Architecture Improvements Applied
| Document | Change | Rationale |
|----------|--------|-----------|
| ADR NNN | ... | ... |

### Vision Items (Flagged for User)
| Finding | Recommendation |
|---------|----------------|
| ... | ... |

### Deferred Improvements
| Finding | Reason | Recommend When |
|---------|--------|----------------|
| ... | ... | ... |

### Files Changed
- [list of files modified]
```

---

## Ecosystem Integration

| Existing Command | How This Command Uses It |
|-----------------|--------------------------|
| `/project:feature-gap` | Step 1 uses its per-component verification logic (service exists, model exists, tests exist) |
| `/project:architecture` | Step 3 uses its ADR-required and drift-detection logic |
| `/project:improve` | Pattern reference — similar ecosystem-review structure |
| `/project:audit` | Similar scan → classify → prioritize → report pattern |
| `/project:reflect` | Similar findings-table output format |

This command does **not** duplicate those commands. It references their logic and reuses their approach where applicable.

## Commit Guideline

RULE (SHOULD ALWAYS FOLLOW): always make git msg of one line in standard manner, and never add any co authored by text never.
