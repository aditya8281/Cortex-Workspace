# /project:health — Repository Health Check

Run weekly or before major milestones. Comprehensive health check across all systems.

## Instructions

**Scope:** Broad ecosystem health — skills, docs, governance, tech debt trends. For deep code-level scanning (runtime errors, dead code, integration issues), use `/project:audit` instead.

1. **Run system validation.**
Run `.agents/plans/shared-phases.md#system-validation`.

2. **Run repository health scan.**
Run `.agents/plans/shared-phases.md#repository-health-scan`.

3. **Check skill health.**
- List all skills in `.agents/skills/`
- For each, check if it has a definition file (`.md`, `.txt`, `.yaml`, `.py`)
- Check last modification date — flag skills not updated in 30+ days as stale
- List any skills that appear unused (no references in docs or workflows)

4. **Check documentation freshness.**
- For each doc in `docs/`, check if it has a "Last updated" date
- Flag docs that reference outdated information (old phase numbers, stale links)
- Check for broken cross-references between docs

5. **Check tech debt hotspots.**
```bash
git log --oneline --since="2 weeks ago" | head -50
```
- Identify files changed 5+ times in recent commits
- Count TODO/FIXME/HACK/XXX/TBD comments in codebase
- List files with the most technical debt indicators

6. **Output** format:

```
## Health Report: [date]

### Hooks: X/N passed
[Per-hook results — N is the total count from run_hooks.py output]

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

7. Save report to `docs/audits/YYYY-MM-DD-health-report.md`.
