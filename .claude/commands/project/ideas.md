# /project:ideas — Innovation and Opportunity Discovery

Run weekly or monthly during planning/strategy sessions. Discovers new features, improvements, and strategic opportunities.

## Instructions

### 0. Load Context

Invoke `cortex-repo-discovery`. Invoke `cortex-repository-intelligence`.

### 1. Analyze Recent Progress

```bash
git log --oneline --since="2 weeks ago"
```

What was built? What patterns emerge? What's accelerating?

### 2. Read the Roadmap

Read `.agents/plans/IMPLEMENTATION_STEPS.md`. What's next? What's partially complete? What's blocked?

### 3. Check Feature Gaps

If a `/project:feature-gap` report exists in `docs/audits/`, read it. Prioritize ideas that address identified gaps.

### 4. Read the Vision

Read the Vision section of `README.md`. What's the gap between current state and the vision?

### 5. Identify Opportunities

| Category | Questions |
|----------|-----------|
| **Feature** | New features to advance vision? Extend existing? Most user value? |
| **Improvement** | Incomplete features? Rough UX? Performance bottlenecks? |
| **Competitive** | Similar projects? Market gaps? Unique advantages? |
| **Capability** | New use cases? Feature composition? Integrations? |
| **Ecosystem** | New skills? New hooks? Automated workflows? |

### 6. Prioritize

P0 (critical, do soon) / P1 (important, next phase) / P2 (valuable, backlog) / P3 (interesting, future)

### 7. Output

```text
## Ideas: [date]

### Progress Analysis
### Vision Gap
### Ideas
| # | Priority | Category | Idea | Effort | Impact |

### Summary
Total: N, P0: N, P1: N, P2: N, P3: N, Top recommendation: ...
```

Save to `docs/ideas/YYYY-MM-DD-{N}.md` if 3+ ideas found.

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:ideas",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
