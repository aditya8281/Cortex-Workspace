# cortex-repo-cleanup

Remove temporary files, dead code, and ensure only intentional changes remain.

## When to Use

Before merge, after implementation, before final commit.

## Process

### 1. Review Changes

```bash
git status
git diff --name-only main
```

### 2. Remove

- Temporary files, scratch files
- Abandoned implementations
- Dead code
- Obsolete comments
- Stale references

### 3. Verify

- Imports are clean
- Documentation references valid
- Configuration consistent
- No TODO/FIXME left intentionally

## Output

Clean working tree with only intentional changes remaining.

## Examples

```
Invoke cortex-repo-cleanup before final commit.
```
