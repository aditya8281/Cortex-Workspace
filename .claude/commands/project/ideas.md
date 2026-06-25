# /project:ideas — Innovation and Opportunity Discovery

Run weekly or monthly during planning/strategy sessions. Discovers new features, improvements, and strategic opportunities.

## Instructions

1. **Analyze recent progress.**
```bash
git log --oneline --since="2 weeks ago"
```
What was built? What patterns emerge? What's accelerating?

2. **Read the roadmap.** Read `docs/ROADMAP.md`. What's next? What's partially complete? What's blocked?

3. **Check feature gaps.** If a `/project:feature-gap` report exists in `docs/audits/`, read it. Prioritize ideas that address identified gaps.

4. **Read the vision.** Read the Vision section of `README.md`. What's the gap between current state and the vision?

5. **Identify opportunities** in each category:

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

6. **Prioritize** each idea:
- **P0** — critical for vision, do soon
- **P1** — important, plan for next phase
- **P2** — valuable, Backlog
- **P3** — interesting, future consideration

7. **Output** format:

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

8. If 3+ ideas found, save to `docs/ideas/YYYY-MM-DD.md`.
