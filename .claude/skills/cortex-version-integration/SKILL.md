# cortex-version-integration

Verify version integration readiness before merge.

## When to Use

Before merge, before release, as final gate.

## Process

### 1. Pre-Merge Gate

- [ ] System validation passes (tests, lint, format, hooks, build)
- [ ] Documentation consistent with changes
- [ ] ADRs created for architectural decisions
- [ ] Progress tracking updated
- [ ] Clean commit history
- [ ] Working tree clean

### 2. Merge Verification

```bash
make hooks-merge
make check
```

## Output

Ready/Not Ready with blocked items listed. Only finalize when all gates pass.

## Examples

```
Invoke cortex-version-integration before merging to main.
```
