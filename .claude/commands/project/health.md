# /project:health — Repository Health Check

Run weekly or before major milestones. Comprehensive health check across all systems.

**Scope:** Broad ecosystem health — skills, docs, governance, tech debt trends. For deep code-level scanning, use `/project:audit`.

## Instructions

### 1. Run System Validation

Invoke `cortex-repo-discovery`. Invoke `cortex-system-validation`.

### 2. Run Repository Health Scan

Invoke `cortex-repo-health-scan`.

### 3. Check Skill Health

- List all skills in `.claude/skills/`
- For each, check if it has a definition file
- Flag skills not updated in 30+ days as stale
- List any unused skills (no references in docs or workflows)

### 4. Check Documentation Freshness

- For each doc in `docs/`, check for "Last updated" date
- Flag outdated references, stale links, broken cross-references

### 5. Check Tech Debt Hotspots

```bash
git log --oneline --since="2 weeks ago" | head -50
```

- Identify files changed 5+ times in recent commits
- Count TODO/FIXME/HACK/XXX/TBD comments
- List files with most tech debt indicators

### 6. Output

```text
## Health Report: [date]

### Hooks: X/N passed
### Automation Health [per-phase]
### Bug Discovery [per-category]
### Skill Health (Total: N, Complete: N, Stale: N, Unused: N)
### Documentation (Total: N, With dates: N, Outdated: N, Broken links: N)
### Tech Debt (Hotspot files: N, TODO/FIXME: N)

### Health Score: X/100
```

### 7. Save Report

Save to `docs/audits/YYYY-MM-DD-health-report-{N}.md`.

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:health",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
