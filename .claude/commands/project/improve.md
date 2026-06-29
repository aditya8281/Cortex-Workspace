# /project:improve — Ecosystem Self-Improvement

Run weekly or after completing significant work. Reviews and enhances skills, hooks, workflows, and governance.

## Instructions

### 0. Load Ecosystem State

Invoke `cortex-repo-discovery`. Invoke `cortex-repository-intelligence`. Invoke `cortex-repo-health-scan`.

### 1. Analyze Ecosystem Feedback

Read `.claude/ecosystem/feedback.json`. This file accumulates structured feedback from every command run across the ecosystem.

#### 1a. Aggregate Feedback Data

For each entry in `feedback.json`:

- **Command frequency:** Which commands run most/least? Commands never run are candidates for removal.
- **Outcome distribution:** Per-command success/failure/partial rates. Commands with >20% failure rate need investigation.
- **Duration trends:** Commands getting slower over time may have growing scope or performance issues.
- **Recurring learnings:** Identify learnings that appear in 3+ entries — these are systemic patterns, not one-offs.
- **Cross-command suggestions:** Suggestions that reference other commands or skills indicate coupling issues or missing integrations.

#### 1b. Identify Ecosystem Patterns

Categorize discovered patterns into:

| Pattern Type | Signal | Example |
|---|---|---|
| **Recurring failure** | Same command fails with same error class 3+ times | `/project:verify` fails on missing migrations |
| **Emerging best practice** | Multiple commands' learnings converge on same approach | "Always run cortex-repo-discovery first" |
| **Scope drift** | Command's actual outcomes diverge from stated purpose | `/project:improve` doing code review instead of ecosystem improvement |
| **Integration gap** | Suggestions reference capabilities that don't exist | "Should check feedback.json" in learnings |
| **Stale command** | No feedback entries in 60+ days | `/project:ideas` hasn't been run |
| **Overloaded command** | Single command generates feedback for 3+ categories | One command doing too many things |

#### 1c. Health Trend Analysis

If `feedback.json` has 5+ entries, compute trends:

- **Ecosystem health score:** `(successful_runs / total_runs) * 100` over last 30 days
- **Improvement velocity:** Are suggestions being addressed? Track suggestion-to-implementation ratio
- **Failure hotspots:** Commands contributing most to ecosystem failure rate
- **Coverage gaps:** Commands suggested but never created

### 2. Review Skill Usage

- Check git log for recent skill invocations
- Which skills from `.claude/skills/` were used? Which skipped? Why?
- Skill creation opportunities not acted on?
- Stale skills (not updated in 30+ days)?

Cross-reference with feedback patterns: if a recurring learning says "should use X skill" but X doesn't exist, propose creating it.

### 3. Review Hook Effectiveness

- Run hooks — any false positives?
- Checks that should be hooks but aren't?
- Hooks producing noisy/irrelevant findings?

Cross-reference with feedback: if feedback entries repeatedly mention issues that hooks should catch, the hook coverage is insufficient.

### 4. Review Workflow Gaps

- Read `.agents/plans/IMPLEMENTATION_STEPS.md`
- Manual steps that could be automated?
- Unclear or incomplete workflows?
- Missing workflows for common tasks?

Cross-reference with feedback: patterns in learnings and suggestions often surface workflow gaps that the docs don't capture.

### 5. Review Documentation

- Check all docs in `docs/` for completeness
- Cross-references valid?
- Topics not covered?

Cross-reference with feedback: if commands consistently report "documentation outdated" in their learnings, prioritize those docs.

### 6. Review Governance Rules

- Read `docs/GOVERNANCE.md`
- Rules needing updating?
- New patterns to codify?

### 7. Propose Command File Improvements

**NEVER auto-apply changes.** Present all proposals as a structured diff/plan.

For each proposed improvement:

```text
### Proposal: [short title]

**Target:** `.claude/commands/project/[name].md`
**Priority:** critical | high | medium | low
**Evidence:** [which feedback entries / patterns justify this]
**Type:** fix | enhance | clarify | deprecate | merge

**Proposed change:**
[exact diff showing old content → new content]

**Risk:** [what could break if applied]
**Validation:** [how to verify the change works]
```

Improvement types:

- **fix:** Command produces errors or wrong output
- **enhance:** Command works but feedback reveals missing capability
- **clarify:** Command instructions are ambiguous (evidenced by varying execution quality)
- **deprecate:** Command is unused or superseded
- **merge:** Two commands overlap and should consolidate

### 8. Propose New Skills

If patterns suggest reusable workflows not yet captured as skills:

```text
### Proposed Skill: [name]

**Evidence:** [feedback patterns that justify this]
**Workflow it captures:** [step-by-step]
**Commands it would serve:** [which commands would invoke this]
**Similar to:** [existing skill, if any, that's close but insufficient]
```

New skill proposals require at least 2 distinct evidence sources (feedback entries, recurring suggestions, or pattern analysis).

### 9. Generation Opportunities

- New command needed? (recurring manual process)
- New hook needed? (recurring quality issue)
- New skill needed? (recurring workflow pattern)

### 10. Output

```text
## Ecosystem Improvement: [date]

### Ecosystem Feedback Analysis
- Total feedback entries: N
- Commands tracked: N
- Success rate: X%
- Recurring patterns identified: N
- [If 5+ entries] Health trend: [improving | stable | declining]

### Top Patterns
| # | Pattern Type | Frequency | Commands Affected | Impact |
| 1 | [recurring failure / best practice / drift / gap / stale / overloaded] | N occurrences | [commands] | [high/medium/low] |

### Skill Review (Used: N, Stale: N, Creation opportunities: N)
### Hook Review (False positives: N, Missing hooks: N, Recommendations: N)
### Workflow Review (Gaps found: N, Recommendations: N)
### Documentation Review (Outdated: N, Missing topics: N, Recommendations: N)
### Governance Review (Updates needed: N, Recommendations: N)

### Command Improvement Proposals (N proposals)
[structured diffs for each proposed command change]

### New Skill Proposals (N proposals)
[skill definitions for each proposed skill]

### Improvement Recommendations
| # | Priority | Category | What | Why | Effort |

### Summary (Total: N, Now: N, Soon: N, Later: N)
```

### 11. Save

If action-items found, save to `docs/audits/YYYY-MM-DD-improve-{N}.md`.

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, analyze ALL entries (not just this command's). Identify cross-command patterns.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:

```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:improve",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<ecosystem patterns discovered>"],
  "suggestions": ["<specific command/skill improvements>"],
  "duration_ms": 0
}
```
