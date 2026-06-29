# /project:update — Project Evolution Orchestrator

**NOT** an implementation command. The **evolution command**. Transforms high-level ideas into implementation-ready project plans through systematic design, validation, and planning integration.

## When to Run

When the user proposes:

- a new feature
- a UI redesign
- a backend redesign
- an architecture change
- a roadmap improvement
- a product vision improvement
- a documentation initiative
- a refactor
- a performance improvement
- a security improvement
- or describes a desired outcome without specifying how

Do **not** run for well-understood tasks that already have a clear spec — `/project:develop` handles those directly.

## Philosophy

```
User says:   "/project:update make Cortex enterprise-ready"
                                             ↓
/project/update:  classify → explore → spec → impact → plan → approve → handoff
                                             ↓
/project/develop:  (later) execute the first milestone
```

| Command | Role | When |
|---------|------|------|
| `/project:update` | Design and plan evolution | High-level idea → approved plan |
| `/project:enhance_plan` | Improve planning ecosystem | Plans drifted from reality |
| `/project:develop` | Execute next iteration | Approved plan → implementation |
| `/project:cortex` | Full implementation cycle | Concrete task → merged code |
| `/project:prompt` | Generate implementation prompt | Complex task needs structured spec |
| `/project:verify` | Automated validation | Pre-merge checks |

This command conceptually invokes those workflows. It does **not** duplicate their instructions.

## How Specification Scales

This command adapts to request complexity:

| Request Scale | Spec Detail | Phases Used | Skill Depth |
|---------------|-------------|-------------|-------------|
| **Simple** (fix auth flow) | 1-page spec, key decisions only | 0→2→3→6 | 1-2 skills |
| **Medium** (streaming memory) | Standard spec with architecture, data model, APIs | 0→1→2→3→4→6 | 2-4 skills |
| **Complex** (desktop redesign) | Full spec with all sections, migration plan, risk analysis | 0→1→2→3→4→5→6 | 4-8 skills |
| **Vision** (enterprise-ready) | Multi-milestone roadmap, phased spec, strategic analysis | 0→1→2→3→4→5→6 | All relevant skills |

Scale automatically. Do not over-generate for simple requests. Do not under-design for complex ones.

## Instructions

---

### Phase 0: Repository Intelligence + Request Classification

#### 0.1 Discover Repository State

Invoke `cortex-repo-discovery` then `cortex-repository-intelligence`. Invoke `cortex-planning-ecosystem`.

Additionally read `docs/ARCHITECTURE.md` and `CLAUDE.md` for execution contract and constraints.

Check whether the requested update **already exists** in plans or implementation:

- Is it in any phase plan? Check all Phase-N.md files for matching keywords.
- Is it in ROADMAP.md? Check roadmap sections.
- Is it already implemented? Check services, models, routers, frontend.
- Has an ADR been written? Check `docs/decisions/`.

If the update already exists in plans → flag it and recommend `/project:develop` to execute.
If the update already exists in code → flag it and suggest updating plans or moving on.
If the update partially exists → note what's done and what's missing.

**Outcome:** Repository intelligence summary. Classification decision. Existence check complete.

#### 0.2 Classify the Request

Classify the user's request to determine:

**Primary category — what kind of change is this?**

| Category | Example Requests | Specification Style |
|----------|-----------------|-------------------|
| **architecture** | migrate to plugin architecture, change provider pattern | Architecture spec, ADR, migration plan |
| **feature** | streaming memory, add MCP server | Feature spec, user stories, data model |
| **redesign** | redesign desktop UI, rework auth flow | Design spec, migration plan, UX spec |
| **refactor** | consolidate parser code, extract service boundary | Refactor plan, interface design, test strategy |
| **performance** | reduce memory usage, optimize retrieval latency | Benchmark spec, optimization plan, metrics |
| **security** | improve auth, add audit logging | Security spec, threat model, hardening plan |
| **roadmap** | reorder versions, add missing milestone | Roadmap update, planning integration, dependency reorder |
| **vision** | make Cortex enterprise-ready, prepare for launch | Strategic spec, phased roadmap, gap analysis |
| **documentation** | rewrite all API docs, add onboarding guide | Documentation plan, audience analysis, structure |
| **ecosystem** | create new skill, add new hook | Ecosystem spec, integration plan, governance update |

**Secondary categories — what else does this touch?**

- backend / frontend / CLI / desktop / agents / data / devops / testing / docs / architecture / planning

**Magnitude — how much change is involved?**

| Magnitude | Indicators | Spec Scale |
|-----------|-----------|------------|
| **small** | Single subsystem, no new models, no migration | Concise (1 page) |
| **medium** | 2-3 subsystems, new models or APIs, small migration | Standard (3-5 pages) |
| **large** | Cross-cutting, new architecture, data migration, multiple phases | Full (5-15 pages) |
| **strategic** | Changes product direction, multi-version, new domain | Vision (15+ pages + roadmap) |

**Fit — does this align with the roadmap?**

- On-roadmap: within scope of an existing version/phase
- Off-roadmap extension: extends scope of existing version but doesn't change direction
- Off-roadmap new: doesn't fit any current version — needs roadmap update
- Contradicts roadmap: actively conflicts with documented direction — flag for discussion

If the request contradicts the roadmap, surface the contradiction clearly. Do not proceed without user acknowledgment.

**Outcome:** Clear classification: primary category, secondary categories, magnitude, roadmap fit.

#### 0.3 Declare the Plan

Present the classification to the user:

```text
## Update Plan: [request summary]

### Classification
- Primary: [category]
- Secondary: [categories]
- Magnitude: [small/medium/large/strategic]
- Roadmap fit: [on-roadmap / extension / new / contradicts]

### Approach
[1-2 sentence description of how the update will be handled]

### Expected Output
- Specification: [concise/standard/full]
- Skills to invoke: [list]
- Planning updates needed: [list]

### Estimated Phases
1. [phase name] — [what it covers]
2. [phase name] — [what it covers]
...

Proceed? (User confirms before continuing.)
```

If the request is ambiguous, ask clarifying questions — the minimum needed to classify it. Do not generate multiple speculative approaches before the user confirms direction.

**Gate:** User confirms the plan before proceeding to Phase 1.

---

### Phase 1: Exploration and Skill Synthesis

#### 1.1 Determine Applicable Skills

Based on the classification, select skills to invoke.

**Always invoke (for any update of medium+ magnitude):**

| Skill | Why |
|-------|-----|
| `brainstorming` | Explores user intent, requirements, design. Always relevant for creative/design work. |

**Conditionally invoke (based on classification):**

| When | Skill | Why |
|------|-------|-----|
| **architecture** | `codebase-design` | Deepening opportunities, interface design, module boundaries |
| **architecture** | `design-an-interface` | Generate multiple interface designs, compare, choose |
| **redesign / UI** | `brainstorming` | Explore design direction before specifying |
| **redesign / UI** | `frontend-design` or `design-taste-frontend` | Premium design guidance |
| **redesign / UI** | `design-md` | Generate semantic design system |
| **vision / complex** | `decision-mapping` | Turn loose idea into sequenced investigation tickets |
| **refactor** | `codebase-design` | Deep module design, interface quality |
| **refactor** | `request-refactor-plan` | Small-commit refactor plan |
| **security** | NA — use threat model, not a skill | Review OWASP patterns, existing auth model |
| **performance** | NA — use benchmarks, metrics | Measure before optimizing |
| **domain / new concept** | `domain-modeling` | Ubiquitous language, terminology, glossary |
| **feature** | `codebase-design` | Interface design for new modules |
| **feature** | `design-an-interface` if ambiguous | Multiple interface approaches |
| **ecosystem** | `writing-great-skills` | Skill quality standards |
| **documentation** | NA — plan structure, don't invoke skills | Audience analysis, content plan |

**Invoke skills** using the Skill tool. Do not read skill files manually.

For each invoked skill, note:
- What it contributed
- What it recommended
- What was accepted or rejected (with rationale)

**Do not invoke implementation skills** (TDD, subagent-driven-development, implement, scaffold-exercises). This phase designs — it does not build.

#### 1.2 Generate Multiple Approaches

For any significant change (medium+ magnitude), generate at least 2-3 distinct approaches before recommending one.

For each approach, evaluate:

| Dimension | Questions |
|-----------|----------|
| **Feasibility** | Can this be built with current infrastructure? What new dependencies? |
| **Complexity** | How many files change? How many subsystems affected? New concepts needed? |
| **Risk** | What could go wrong? Migration cost? Backward compatibility? |
| **User impact** | How does this change the user experience? Is there migration burden? |
| **Maintainability** | Is the new approach easy to modify? Does it add conceptual weight? |
| **Alignment** | Does it follow the constitution (guide.md) principles? |
| **Future-proofing** | Does it enable or block future work? |

For **small** changes, skip multi-approach generation. A single recommended approach with rationale is sufficient.

For **medium** changes, generate 2 approaches and recommend one.

For **large** changes, generate 2-3 approaches and score them.

For **strategic** changes, generate 3+ approaches, score each, and optionally use `decision-mapping` skill to create investigation tickets for unresolved questions.

#### 1.3 Recommend the Strongest Approach

Present approaches and recommendation:

```text
## Exploration: [request]

### Approach A: [name]
[2-3 sentence summary]
- Feasibility: [high/medium/low]
- Complexity: [S/M/L]
- Risk: [low/medium/high]
- User impact: [positive/neutral/negative]
- Alignment: [strong/moderate/weak]

### Approach B: [name]
...

### Recommendation
**Recommended:** Approach [letter] — [1-2 sentence rationale]

### Key Decisions
- [Decision 1 with rationale]
- [Decision 2 with rationale]

### Open Questions
- [Question 1 — resolved by spec phase]
- [Question 2 — needs research]
```

**Outcome:** Recommended approach with rationale. Skills applied. Decisions documented.

---

### Phase 2: Specification

Produce a complete specification for the approved approach.

Scale the spec to match the request magnitude (see table in Philosophy section above).

The spec is modular — include only sections relevant to the request.

#### Spec Template (Use Relevant Sections Only)

```markdown
# Specification: [Update Name]

**Date:** YYYY-MM-DD
**Status:** Draft for approval
**Author:** Cortex AI

---

## 1. Motivation

### Problem Statement
[What problem does this solve? What is the current state that's insufficient?]

### User Value
[How does this make Cortex better for users?]

### Developer Value
[How does this make the codebase better for developers?]

### Product Fit
[How does this align with Cortex vision (guide.md §1-2)?]

---

## 2. Goals

### Primary Goals
- [Goal 1]
- [Goal 2]

### Non-Goals (Explicitly Out of Scope)
- [What is explicitly NOT being solved by this update]
- [What is deferred to future updates]

### Success Criteria
| Criterion | How to Measure |
|-----------|---------------|
| ... | ... |

---

## 3. Scope

### In Scope
- [System/subSystem — what changes]
- [System/subSystem — what changes]

### Out of Scope
- [System — not changing]
- [System — deferred]

### Affected Users
[Which user groups are affected and how?]

---

## 4. Architecture

[Only if the update involves architecture changes]

### Current Architecture
[How it works today — concise, reference existing docs]

### Proposed Architecture
[How it will work after the update]

```
[Architecture diagram — ASCII or referenced doc]
```

### Key Design Decisions

| Decision | Option Selected | Alternatives | Rationale |
|----------|----------------|--------------|-----------|
| ... | ... | ... | ... |

### Principles Applied
[How the constitution (guide.md) principles influenced the design]

---

## 5. Components

[Only if the update involves new or changed components]

### New Components
| Component | Purpose | Location | Key Interface |
|-----------|---------|----------|--------------|
| ... | ... | `path/` | ... |

### Modified Components
| Component | Change | Location |
|-----------|--------|----------|
| ... | ... | `path/` |

### Removed Components
| Component | Replacement | Migration |
|-----------|-------------|-----------|
| ... | ... | ... |

---

## 6. Data Model

[Only if the update involves data model changes]

### New Models
| Model | Fields | Key Constraints |
|-------|--------|-----------------|
| ... | ... | ... |

### Modified Models
| Model | Change | Migration Required? |
|-------|--------|---------------------|
| ... | ... | Yes/No |

### Migration Plan
[How existing data is migrated. Include rollback plan.]

---

## 7. API Changes

[Only if the update involves API changes]

### New Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| ... | ... | ... |

### Modified Endpoints
| Method | Path | Change |
|--------|------|--------|
| ... | ... | ... |

### Deprecated Endpoints
| Method | Path | Replacement | Migration |
|--------|------|-------------|-----------|
| ... | ... | ... | ... |

---

## 8. UI/UX Changes

[Only if the update involves frontend or UI changes]

### Before/After
[Description of what changes visually]

### New Screens or Components
| Screen/Component | Purpose | Route |
|------------------|---------|-------|
| ... | ... | `app/...` |

### Design Principles
[How the Warm Neural Dark design system is applied or extended]

---

## 9. Security Implications

[Only if the update touches security-sensitive areas]

### Threat Model
[What threats exist for the new functionality?]

### Security Controls
| Control | Purpose |
|---------|---------|
| ... | ... |

### Privacy Impact
[Does this change affect data privacy? Is any data newly exposed?]

---

## 10. Performance Implications

### Expected Impact
[How does this change affect performance? Better, worse, neutral?]

### Benchmarks
[Baseline measurements and targets]

### Optimization Opportunities
[What can be optimized if needed]

---

## 11. Testing Strategy

### Unit Tests
- New test files needed: [count/names]
- Existing tests to update: [count/names]

### Integration Tests
- New integration tests: [what they cover]

### Migration Tests
- Tests for data migration

### Performance Tests
- Benchmarks to run

---

## 12. Migration Plan

[Only if the update requires migration]

### Breaking Changes
| Change | Impact | Migration |
|--------|--------|-----------|
| ... | ... | ... |

### Migration Steps
1. ...
2. ...

### Rollback Plan
[How to revert if migration fails]

### Backward Compatibility Period
[How long old paths are supported]

---

## 13. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ... | L/M/H | L/M/H | ... |

### Unknowns
- [Known unknowns that need investigation]

---

## 14. Alternatives Considered

| Alternative | Why Not Selected |
|-------------|------------------|
| ... | ... |

---

## 15. Implementation Estimate

### Phases
| Phase | Description | Files | Effort | Dependencies |
|-------|-------------|-------|--------|--------------|
| 1 | ... | ~N | X days | None |
| 2 | ... | ~N | X days | Phase 1 |
| 3 | ... | ~N | X days | Phase 2 |

### Total Estimate
[Summary of effort across all phases]

### Dependencies
- [External dependencies]
- [Internal dependencies]

---

## 16. Documentation Plan

| Document | Action |
|----------|--------|
| `docs/ARCHITECTURE.md` | Update architecture section |
| `CLAUDE.md` | Add new patterns |
| `docs/API.md` | Add new endpoints |
| `docs/DATABASE.md` | Add new models |
| ADR | Create new ADR for key decisions |
```

**Include only the sections relevant to the request.** Skip sections that don't apply. The spec must be complete enough to make an implementation decision, but no longer than necessary.

**Outcome:** Complete specification. Scaled to request complexity.

---

### Phase 3: Repository Impact Analysis

Determine every system, file, and artifact that the update affects.

#### 3.1 Scan All Ecosystem Layers

Run:

```bash
# Available layers to check
ls .claude/commands/project/
ls .claude/skills/ 2>/dev/null | head -20
ls .claude/hooks/ 2>/dev/null
ls docs/ 2>/dev/null
```

Check each layer for required updates:

| Layer | Action | What to Look For |
|-------|--------|------------------|
| **Roadmap** | `.agents/plans/IMPLEMENTATION_STEPS.md` | Does the roadmap need a new version/phase? Do existing phases need reordering? |
| **Version plans** | `.agents/plans/versions/v*/Phase-*.md` | Do any existing phase plans need updating? Is this a new phase? |
| **Progress** | `.agents/plans/versions/v*/progress.md` | Will progress tracking need new component rows? |
| **Implementation steps** | `.agents/plans/IMPLEMENTATION_STEPS.md` | Does the execution order change? |
| **Cross-reference** | `.agents/plans/FinalCompatibilities.md` | Does the reference architecture mapping change? |
| **Architecture** | `.agents/plans/GUIDE.md` | Do architecture principles or decisions change? |
| **Commands** | `.claude/commands/project/*.md` | Do any commands need updating? New command needed? |
| **Hooks** | `.claude/hooks/` | Does validation need new hooks? |
| **Governance** | `docs/GOVERNANCE.md` | Do governance rules or security patterns change? |
| **Skills** | `.claude/skills/` | Is a new skill needed? Does an existing skill need updating? |
| **CLAUDE.md** | `CLAUDE.md` | Do architecture constraints change? New patterns? |
| **ADRs** | `docs/decisions/` | Is a new ADR needed? Do existing ADRs get superseded? |
| **Tests** | `tests/` | What test files are affected? New test directories needed? |
| **Configuration** | `pyproject.toml`, `package.json`, Docker, env | Are new dependencies needed? Configuration changes? |

#### 3.2 Compile Impact Table

```text
## Repository Impact

### Plans
| Document | Action Required | Notes |
|----------|----------------|-------|
| `implementation_steps.md` | [Update / No change] | ... |
| `ACTIVE_VERSION.md` | [Update / No change] | ... |
| `versions/v{N}/Phase-{M}.md` | [Update / New phase / No change] | ... |

### Ecosystem
| System | Action Required | Notes |
|--------|----------------|-------|
| Commands | [New / Update / None] | ... |
| Hooks | [New / Update / None] | ... |
| Skills | [New / Update / None] | ... |
| Workflows | [Update / None] | ... |
| Prompts | [New / Update / None] | ... |
| Templates | [New / Update / None] | ... |

### Documentation
| Document | Action Required | Notes |
|----------|----------------|-------|
| `CLAUDE.md` | [Update / No change] | ... |
| `docs/ARCHITECTURE.md` | [Update / No change] | ... |
| `docs/API.md` | [Update / No change] | ... |
| `docs/DATABASE.md` | [Update / No change] | ... |
| `docs/GOVERNANCE.md` (Security) | [Update / No change] | ... |

### Implementation
| Area | Files Changed | Notes |
|------|-------------|-------|
| Backend services | ~N | ... |
| Backend models | ~N | ... |
| Backend routers | ~N | ... |
| Frontend | ~N | ... |
| CLI | ~N | ... |
| Tests | ~N | ... |
| Migrations | ~N | ... |

### Configuration
| File | Action Required |
|------|----------------|
| `pyproject.toml` | [New dependency / No change] |
| `package.json` | [New dependency / No change] |
| `Dockerfile` / `docker-compose.yml` | [Update / No change] |
| Environment variables | [New var / No change] |
```

**Outcome:** Complete repository impact table. No ecosystem layer missed.

---

### Phase 4: Planning Ecosystem Integration

Conceptually invoke the `/project:enhance_plan` workflow.

Use the approved spec and impact analysis as context to improve the planning ecosystem.

#### 4.1 Check Planning Consistency

Before making changes, verify:

- Does the roadmap accurately reflect where this update fits?
- Are there any planning contradictions this update creates or resolves?
- Are version boundaries still appropriate, or does this update warrant a new version?
- Do phase plans need new deliverables or modified scope?
- Do exit criteria for current/adjacent phases need updating?
- Are there dependencies that need reordering?

#### 4.2 Apply Planning Improvements

Update planning artifacts to integrate the update:

**For a milestone within an existing phase:**
- Add component rows to `progress.md`
- Update phase plan exit criteria if scope changed

**For a new phase in an existing version:**
- Update `ACTIVE_VERSION.md` if this becomes the active phase
- Create new Phase-N.md with deliverables, architecture, dependencies, exit criteria
- Update `implementation_steps.md` version summary if deliverables changed
- Update `ROADMAP.md` phase table

**For a new version:**
- Create version directory under `versions/v{N+1}/`
- Create Phase-1.md for the new version
- Create `progress.md` for the new version
- Create `features.md` if this version has feature-level detail
- Update `ACTIVE_VERSION.md` to point to the new version
- Update `implementation_steps.md` to include the new version
- Update `ROADMAP.md` version timeline
- Check FinalCompatibilities.md for any new reference architecture mappings

**For architecture changes that affect existing plans:**
- Update `guide.md` architecture section if principles change
- Create or update ADRs for key decisions
- Cross-reference against all existing phase plans that may be affected

**For roadmap reordering:**
- Update `ROADMAP.md` with new phase/version order
- Update `implementation_steps.md` if execution order changes
- Check all downstream plans for broken dependencies
- Add rationale for reordering

#### 4.3 Remove Inconsistencies

After applying changes, verify:

- ROADMAP.md phase names match actual Phase-N.md files
- Test counts in all documents match reality (`pytest --collect-only`)
- Version/phase status in ROADMAP.md matches ACTIVE_VERSION.md
- No phase plan references components that were removed
- ADR numbering is sequential

**Outcome:** Planning ecosystem reflects the approved update. Roadmap, phases, and plan documents are consistent.

---

### Phase 5: Adversarial Review

Before seeking approval, stress-test the specification.

Invoke `cortex-adversarial-challenge` to challenge completeness, feasibility, risks, coherence, and scale.

After the skill completes, present challenges:

```text
## Adversarial Review

### Challenges
| # | Severity | Challenge | Recommendation |
|---|----------|-----------|---------------|
| 1 | medium | ... | ... |
| 2 | low | ... | ... |

### Resolved
| Challenge | Resolution |
|-----------|------------|
| ... | ... |

### Impact on Spec
[Summary of any spec changes from the review]
```

Resolve challenges and update the spec before presenting for approval.

**Outcome:** Updated spec that has survived adversarial review.

---

### Phase 6: Approval

Present the complete package for user approval.

#### 6.1 Present Summary

```text
## Update Proposal: [Name]

**Magnitude:** [small/medium/large/strategic]
**Spec sections:** [list of sections included]
**Planning changes:** [summary]

---

### Specification
[Link to or embed the full spec from Phase 2]

---

### Repository Impact
[Impact table from Phase 3]

---

### Planning Changes
[Summary of planning ecosystem updates from Phase 4]

- [Change 1]
- [Change 2]

---

### Adversarial Review
[Summary of challenges and resolutions from Phase 5]

---

### Implementation Estimate
| Phase | Description | Effort | Dependencies |
|-------|-------------|--------|--------------|
| 1 | ... | X days | None |
| 2 | ... | X days | Phase 1 |
| 3 | ... | X days | Phase 2 |

**Total:** X-Y days

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ... | L/M/H | L/M/H | ... |

### Alternatives
| Alternative | Why Not Selected |
|-------------|-----------------|
| ... | ... |

---

**Approve?** (User must confirm before implementation.)
```

#### 6.2 Approval Gate

**Do not proceed to implementation until the user approves.**

If the user rejects or requests changes:

- Update the spec based on feedback
- Return to Phase 3 or 4 as needed
- Re-present for approval

If the user approves:

- Proceed to Phase 7

**Gate:** User approval received.

---

### Phase 7: Development Handoff

After approval and planning integration:

**Do not implement automatically.**

Generate a development handoff suitable for `/project:develop`.

#### 7.1 Handoff Document

```text
## Development Handoff: [Update Name]

**Approved:** YYYY-MM-DD
**Spec:** [reference to saved spec]

---

### Approved Update Summary
[2-3 sentence summary of what was approved]

### Planning Changes Applied
- [Change 1]
- [Change 2]

### Ecosystem Changes Applied
- [CLAUDE.md update]
- [New ADR]
- [Progress tracking update]

### Repository Impact Summary
- Backend: ~N files
- Frontend: ~N files  
- Tests: ~N files
- Docs: ~N files
- Config: ~N files

---

### First Implementation Milestone

The first thing `/project:develop` should execute:

**Milestone:** [name]
**Objective:** [clear one-line objective]
**Scope:**
- [File 1] — [change]
- [File 2] — [change]
- [File 3] — [change]

**Exit criteria:**
- [Criterion 1]
- [Criterion 2]

**Depends on:**
- [Nothing / specific dependency]

---

### Development Brief

```markdown
## Execution Brief

### Task
[One-line description — what `/project:develop` will execute]

### Scope
- Files likely affected:
- Modules involved:
- Known unknowns:

### Approach
[Brief implementation strategy — 3-5 sentences]

### Dependencies
[What must exist before this work can begin]

### Risks
[What could go wrong]
```

---

### Final Instructions

Planning integration is complete.

The repository roadmap, documentation, and implementation plans are now aligned with the approved update.

Continue implementation using:

```
/project:develop
```
---

#### 7.2 Save Artifacts

Save the spec and handoff to the audit log:

```text
docs/audits/YYYY-MM-DD-update-{N}-spec.md    — The full specification
docs/audits/YYYY-MM-DD-update-{N}-handoff.md — The development handoff
```

Where {N} is the update number for that day.

Do **not** save every artifact. Save only:
- The spec (Phase 2 output) — if it contains non-obvious decisions worth preserving
- The handoff (Phase 7 output) — always, as it's the entry point for `/project:develop`

**Outcome:** Handoff delivered. Planning aligned. Artifacts saved. User instructed to use `/project:develop`.

---

## Full Phase Quick-Reference

| Phase | Purpose | Key Output | Gate |
|-------|---------|-----------|------|
| **0** | Intelligence + Classification | Classification, existence check, plan | User confirms plan |
| **1** | Exploration + Skill Synthesis | Approaches, recommendation, decisions | Internal |
| **2** | Specification | Complete spec, scaled to complexity | Internal |
| **3** | Repository Impact | Full impact table | Internal |
| **4** | Planning Integration | Updated roadmap, plans, progress | Internal |
| **5** | Adversarial Review | Challenges, resolutions | Internal |
| **6** | Approval | Summary for user decision | **User approves** |
| **7** | Handoff | Development handoff for `/project:develop` | Final |

## Ecosystem Integration

| Existing System | How This Command Uses It |
|----------------|--------------------------|
| `/project:enhance_plan` | Phase 4 conceptually invokes its planning drift detection and improvement logic |
| `/project:develop` | Phase 7 generates a handoff that `/project:develop` executes |
| Brainstorming skill | Phase 1 — creative exploration of approaches and trade-offs |
| Codebase Design skill | Phase 1 — interface design, module boundaries, deepening |
| Design an Interface skill | Phase 1 — multiple interface approaches when design is ambiguous |
| Decision Mapping skill | Phase 1 — investigation tickets for complex/vision-level updates |
| Domain Modeling skill | Phase 1 — ubiquitous language for new domain concepts |
| Design skills | Phase 1 — UI/UX design guidance for redesign requests |
| Architecture audit skill | Phase 3 — architecture drift verification |
| `/project:feature-gap` | Phase 3 — per-component verification logic |
| `/project:architecture` | Phase 3 — ADR-required check, drift detection |
| `/project:challenge` | Phase 5 — adversarial review approach |
| `/project:prompt` | Generation model (discover, classify, clarify) used throughout |
| `docs/decisions/` | Phase 3 — ADR creation and cross-reference |
| `.agents/plans/` | Phase 4 — planning artifact updates |
| `CLAUDE.md` | Phase 3 — pattern updates, constraint registration |

This command does **not** duplicate those systems. It invokes, references, and composes them.

## Commit Guideline

RULE (SHOULD ALWAYS FOLLOW): always make git msg of one line in standard manner, and never add any co authored by text never.

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:update",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
