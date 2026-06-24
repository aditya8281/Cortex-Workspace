# /project:health — Repository Health Check

Run weekly or before major milestones. Comprehensive health check across all systems.

## Instructions

1. **Run all hooks.**
```bash
python3 .claude/hooks/run_hooks.py
```
Report: pass/fail per hook, findings.

2. **Run automation health checks.**
```bash
python3 scripts/automation/run_all.py health
```
Report: dead code, duplicates, dependencies, drift.

3. **Run bug discovery.**
```bash
python3 scripts/automation/run_all.py bug-discovery
```
Report: placeholders, security issues, error patterns.

4. **Check skill health.**
- List all skills in `.agents/skills/`
- For each, check if it has a definition file (`.md`, `.txt`, `.yaml`, `.py`)
- Check last modification date — flag skills not updated in 30+ days as stale
- List any skills that appear unused (no references in docs or workflows)

5. **Check documentation freshness.**
- For each doc in `docs/`, check if it has a "Last updated" date
- Flag docs that reference outdated information (old phase numbers, stale links)
- Check for broken cross-references between docs

6. **Check tech debt hotspots.**
```bash
git log --oneline --since="2 weeks ago" | head -50
```
- Identify files changed 5+ times in recent commits
- Count TODO/FIXME/HACK/XXX/TBD comments in codebase
- List files with the most technical debt indicators

7. **Output** format:

```
## Health Report: [date]

### Hooks: X/11 passed
[Per-hook results]

### Automation Health
[Per-phase results]

### Bug Discovery
[Per-category results]

### Skill Health
- Total: N
- Complete: N
- Stale: N
- Unused: N

### Documentation
- Total: N
- With dates: N
- Outdated: N
- Broken links: N

### Tech Debt
- Hotspot files: N
- TODO/FIXME count: N
- Recommendations: N

### Health Score: X/100
```

8. Save report to `docs/audits/YYYY-MM-DD-health-report.md`.
