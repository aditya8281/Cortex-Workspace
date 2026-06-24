# /project:challenge — Adversarial Review

Run this before implementing a significant feature or making an architectural choice. Actively tries to poke holes in the current approach.

## Instructions

1. **Read the current plan/spec/design.** Check for:
- `docs/superpowers/specs/` — latest design spec
- `docs/superpowers/plans/` — latest implementation plan
- Recent git commits — what's being worked on

2. **Challenge the approach.** For each challenge, be specific — reference actual code, actual dependencies, actual constraints.

### Risks and Failure Modes
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
