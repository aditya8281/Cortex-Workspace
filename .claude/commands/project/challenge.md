# /project:challenge — Adversarial Review

Run before implementing a significant feature or making an architectural choice. Actively tries to poke holes in the current approach.

## Instructions

### 1. Read Context

Invoke `cortex-repo-discovery`. Read:
- `.agents/plans/` — latest implementation plan (source of truth)
- Recent git commits — what's being worked on

### 2. Run Adversarial Challenge

Invoke `cortex-adversarial-challenge` for risks, edge cases, over/under-engineering, assumptions, version boundaries, and principle alignment.

### 3. Additional: Unexplored Alternatives

- What other approaches were considered?
- What would a different architecture look like?
- What do similar projects do?

### 4. CORTEX Principle Alignment

- **Privacy-first:** External data leaks?
- **Compound learning:** Contributes to or hinders knowledge accumulation?
- **Two-tier trust:** Respects account/vault separation?
- **Graceful degradation:** Works when optional services unavailable?
- **Model freedom:** Locks into specific model/provider?
- **Living knowledge:** Connects to or fragments knowledge graph?

### 5. Output

```text
## Challenge: [date]

### Approach Being Challenged
### Challenges
| # | Severity | Category | Challenge | Alternative |

### CORTEX Principle Alignment
| Principle | Status | Notes |

### Summary
Critical: N | Warning: N | Nit: N
```

Challenges are advisory — they inform, not block.
