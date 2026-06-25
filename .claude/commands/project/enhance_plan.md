# /project:enhance_plan — Planning Ecosystem Improver

**NOT** implementation. Reviews entire planning ecosystem and improves it — filling gaps between current state, vision, roadmap, architecture, and docs.

## When to Run

After completing a significant phase/version, or when plans show inconsistencies.

## Philosophy

Four dimensions:

| Dimension | Detects | Improves |
|-----------|---------|----------|
| **Implementation drift** | Code exists but plan says not started | Update progress, close milestones |
| **Planning drift** | Plan says done but code missing | Find gaps, add to backlog |
| **Architecture drift** | Implementation diverged from design | Update ADRs, guide.md |
| **Vision drift** | Roadmap doesn't reflect direction | Flag for user, never change automatically |

**Never change product vision.** Flag vision drift for user decision.

## Instructions

### Step 0: Load Planning Ecosystem

Invoke `cortex-repo-discovery`. Invoke `cortex-planning-ecosystem`.

Also review: `.claude/commands/project/`, `.agents/skills/INDEX.md`, `docs/WORKFLOWS.md`, `docs/GOVERNANCE.md`, relevant ADRs.

**Outcome:** Complete understanding of planned state vs actual state.

---

### Step 1: Scan for Implementation Drift

For each component in every active/upcoming phase plan, check:

| Check | How |
|-------|-----|
| Service exists? | `ls backend/app/services/<name>.py` |
| Model exists? | `ls backend/app/models/<name>.py` |
| Router exists? | `ls backend/app/api/v1/<name>.py` |
| Tests exist? | `ls tests/test_<name>.py` |

Also check reverse drift: **code exists but plan says not started**. Grep progress.md for "not started", verify against filesystem. Check test counts match `pytest --collect-only`.

**Outcome:** Map of what's implemented vs what plans claim.

---

### Step 2: Scan for Planning Drift

Compare plans against each other:

1. **ROADMAP.md vs phase plans** — Phase names, statuses, version descriptions match?
2. **ACTIVE_VERSION.md vs progress.md** — Active version/phase matches?
3. **implementation_steps.md vs phase plans** — Deliverables match?
4. **FinalCompatibilities.md vs phase plans** — Cross-reference still accurate?
5. **Phase plans across versions** — Contradictions between V1 and V2?
6. **Version transition criteria** — Documented?
7. **Exit criteria currency** — Still match deliverables?

**Outcome:** Map of planning inconsistencies.

---

### Step 3: Scan for Architecture Drift

Invoke `cortex-architecture-drift`.

Also check `docs/decisions/READMe.md` for ordering. Verify ADR decisions still reflected in codebase. Mark superseded ADRs. Identify undocumented decisions needing new ADRs.

**Outcome:** Map of architecture drift and ADR gaps.

---

### Step 4: Classify and Prioritize Findings

Organize into four **separate** categories:

```
## Implementation Improvements (update code or plan)
## Planning Improvements (update plans only)  
## Architecture Improvements (update ADRs/guide.md only)
## Vision Improvements (flagged for user — never auto-change)
```

Severity: action-item (fix now) / suggestion (quality) / insight (record only)

---

### Step 5: Brainstorm Improvements

Before making changes, consider:
- Can execution order be improved?
- Developer experience friction?
- Missing milestones?
- Documentation gaps?
- Feature gaps from FinalCompatibilities.md?

For each: what problem does it solve? Worth overhead? Aligns with guide.md?

**Outcome:** Applied improvements + deferred ones documented.

---

### Step 6: Apply Improvements

Rules:
- Never change product vision
- Update plans to match code, not reverse
- Keep progress.md accurate
- Keep ROADMAP.md accurate
- Update test counts everywhere
- Update ACTIVE_VERSION.md if phase changed
- Create ADRs for undocumented decisions

Document each change with what, why, which artifact.

**Outcome:** All action-items resolved. Planning ecosystem reflects reality.

---

### Step 7: Enhancement Report

```text
## Planning Enhancement: date

### Summary
- Implementation drift: N
- Planning drift: N
- Architecture drift: N
- Vision drift: N (flagged)
- Applied: N, Deferred: N

### Implementation Improvements Applied | Plan | Change | Rationale |
### Planning Improvements Applied | Document | Change | Rationale |
### Architecture Improvements Applied | Document | Change | Rationale |
### Vision Items (Flagged for User) | Finding | Recommendation |
### Deferred Improvements | Finding | Reason | Recommend When |
### Files Changed
```
