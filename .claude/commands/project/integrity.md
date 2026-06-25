# /project:integrity — Core Repository Integrity System

Thin orchestrator. Calls `IntegrityService` — never accesses engines directly.

**Usage:**
- `/project:integrity` — Full analysis (all engines, full repo)
- `/project:integrity quick` — Quick scan (structural only, changed files)
- `/project:integrity verify` — Verification mode (structural + semantic)
- `/project:integrity full` — All available engines
- `/project:integrity incremental <paths>` — Changed files + transitive deps

**Execution:**
1. Invoke `cortex-repo-discovery` to find repo root
2. Call `IntegrityService(repo_root).analyze(profile=...)`
3. Output findings via Reporter (markdown for CLI, JSON for automation)

## Example Output
```markdown
# Integrity Report
- Total findings: 3
- By severity: CRITICAL: 0, HIGH: 1, MEDIUM: 2
- Execution time: 423ms
```
