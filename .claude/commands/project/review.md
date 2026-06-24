# /project:review — Code Quality Review

Run this before pushing code or creating a PR. Reviews changed code for correctness, patterns, and completeness.

## Instructions

1. **Identify changed files.** Run `git diff --name-only HEAD~1` and `git diff HEAD~1` to see all changes.

2. **Run linting and tests.**
- Run: `make lint`
- Run: `make test`
- Report pass/fail for each.

3. **Review each changed file** for:

### Correctness
- Missing error handling (bare `except:`, swallowed exceptions)
- Off-by-one errors, null checks, type mismatches
- Race conditions, resource leaks

### API Patterns
- Missing `response_model=` on API endpoint decorators
- Missing ownership checks (`resource.user_id == current_user.id`) on user-scoped endpoints
- Routes not in correct order (specific before parameterized)
- Missing router registration in `api/router.py`

### Code Quality
- Hardcoded values that should be in config
- Missing docstrings on public functions
- Overly complex logic that could be simplified
- Dead code or unused imports

### Testing
- New functions/classes without tests
- Edge cases not covered
- Missing integration tests for API endpoints

### Documentation
- New/changed APIs not reflected in docs/API.md
- New models not reflected in docs/DATABASE.md
- Architecture changes not reflected in docs/ARCHITECTURE.md

4. **Output** format:

```
## Code Review: [date]

### Lint: PASS/FAIL
### Tests: PASS/FAIL

### Findings
| # | Severity | File:Line | Issue | Fix |
|---|----------|-----------|-------|-----|
| 1 | P0 | path/to/file.py:42 | ... | ... |

### Summary
- P0 (critical): N
- P1 (important): N
- P2 (minor): N
- Clean: N files
```

5. **Block push** if any P0 findings exist. P1/P2 are advisory.
