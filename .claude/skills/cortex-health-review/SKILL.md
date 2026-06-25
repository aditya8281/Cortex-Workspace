# CORTEX Health Review

Run a comprehensive health check on the Cortex repository.

## When to Use

- Weekly maintenance
- Before release preparation
- When code quality concerns arise
- On request via `/project:health`

## Checks

1. **Dead Code** — unused functions, unreachable code
2. **Duplicate Code** — similar patterns in different files
3. **Technical Debt** — TODOs, FIXMEs, HACKs
4. **Documentation Drift** — docs out of sync with code
5. **Test Coverage** — gaps in test coverage
6. **Dependency Health** — outdated or vulnerable dependencies
7. **Hook Health** — governance hooks passing
8. **Lint Health** — ruff/mypy clean

## Steps

1. Run `make lint` for lint/type check
2. Run `make test` for test health
3. Run `python .claude/hooks/run_hooks.py repo-health` for health hooks
4. Run `python .claude/hooks/run_hooks.py completion-gate` for gate checks
5. Grep for TODOs/FIXMEs in codebase
6. Check documentation files for staleness
7. Generate health report

## Output Format

```markdown
# Health Review: YYYY-MM-DD

## Overall Health: [GOOD | WARNING | CRITICAL]

## Metrics
- Lint: PASS/FAIL
- Tests: PASS/FAIL
- Hooks: N/M passing
- TODOs: N found
- FIXMEs: N found

## Findings
### [SEVERITY] Finding title
- **File:** path/to/file.py:line
- **Description:** What's wrong
- **Fix:** How to fix it
- **Status:** Open | Fixed
```
