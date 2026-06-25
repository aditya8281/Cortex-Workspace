# cortex-documentation-consistency

Cross-reference every doc against current codebase to identify drift.

## When to Use

Before release, after implementation, during health check.

## Process

### 1. Check List

| Check | How |
|-------|-----|
| New/changed APIs reflected in `docs/API.md` | Read API.md, check for API changes in code |
| New models reflected in `docs/DATABASE.md` | Read DATABASE.md, check for model changes |
| Architecture changes in `docs/ARCHITECTURE.md` | Read ARCHITECTURE.md, check for drift |
| ADR created for architectural decisions | Check docs/decisions/ for relevant ADRs |
| README.md reflects current state | Quick scan of README.md |
| Cross-references valid | Check links in docs reference real files |

### 2. For Each Outdated Document

- What changed in code that the doc doesn't reflect
- Which sections need updating
- Severity: actionable / suggestion / insight

## Output

Every outdated document identified, with recommended updates.

## Examples

```
Invoke cortex-documentation-consistency before release.
```
