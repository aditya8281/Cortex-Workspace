# /project:review — Code Quality Review

Run before pushing code or creating a PR. Reviews changed code for correctness, patterns, completeness.

## Instructions

**Scope:** Code quality. For automated pass/fail checks (tests, lint, build), use `/project:verify`.

### 1. Identify Changed Files

Invoke `cortex-repo-discovery`.

```bash
git diff --name-only HEAD~1
git diff HEAD~1
```

### 2. Run Lint and Tests

```bash
make lint
make test
```

Report pass/fail for each.

### 3. Engineering Review

Invoke `cortex-engineering-review` for correctness, API patterns, code quality, and testing review.

### 4. Documentation Check

- New/changed APIs reflected in docs/API.md?
- New models reflected in docs/DATABASE.md?
- Architecture changes reflected in docs/ARCHITECTURE.md?

### 5. Output

```text
## Code Review: [date]

### Lint: PASS/FAIL
### Tests: PASS/FAIL

### Findings
| # | Severity | File:Line | Issue | Fix |

### Summary
- P0 (critical): N
- P1 (important): N
- P2 (minor): N
- Clean: N files
```

**Block push** if any P0 findings exist. P1/P2 are advisory.
