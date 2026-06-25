# cortex-repo-health-scan

Scan repository for health indicators: hooks, skills, tech debt, documentation freshness.

## When to Use

Weekly health check, before release, quality concerns.

## Process

### 1. Hook Health

```bash
uv run python .claude/hooks/run_hooks.py 2>/dev/null || python3 .claude/hooks/run_hooks.py 2>/dev/null
```

Report: pass/fail per hook, any false positives.

### 2. Skill Health

- List all skills in `.claude/skills/`
- Check for definition files in each
- Flag skills not updated in 30+ days as stale
- Flag skills with no references in docs/workflows as unused

### 3. Tech Debt Hotspots

```bash
git log --oneline --since="2 weeks ago" | head -30
```

- Files changed 5+ times in recent commits
- TODO/FIXME/HACK count across codebase
- Files with most tech debt indicators

### 4. Documentation Freshness

Check each doc in `docs/` for:
- "Last updated" date
- Outdated references
- Broken cross-references

## Output

Health status across hooks, skills, tech debt, documentation.

## Examples

```
Invoke cortex-repo-health-scan for weekly health report.
```
