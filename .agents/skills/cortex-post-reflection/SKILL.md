# cortex-post-reflection

Run systematic reflection after completing work.

## When to Use

After implementation, before marking complete, before merge.

## Process

### 1. Identify Work Completed

```bash
git diff --stat HEAD~1
```

Summarize: files changed, features, fixes, refactors, tests, docs.

### 2. Quality

- Code cleanliness, error handling, edge cases, naming, comments
- Functions that do too much, responsibilities well separated?

### 3. Redundancy

- Duplication across files, consolidation opportunities
- Similar abstractions that could be unified
- Repeated literals that should be constants

### 4. Automation

- Manual steps remaining?
- Make target opportunities?
- Hook candidates?

### 5. Skill/Hook/Workflow Opportunities

- New reusable patterns?
- Automation candidates?
- Documentation gaps?

### 6. Documentation Gaps

- Check every file under `docs/` against code changes
- Identify outdated docs, missing topics, stale links

### 7. Technical Debt

- TODOs, shortcuts, postponed refactors, known limitations
- Estimate future cost if unresolved

### 8. Test Gaps

- Missing coverage, edge cases not tested
- Integration test gaps

### 9. Consistency

- Naming, formatting, error handling, typing patterns

### 10. Regression Risk

- Dependencies, integration points, backward compatibility

### 11. Ecosystem Impact

- Commands, hooks, workflows, skills needing updates

## Output

Table of findings with severity: insight / suggestion / action-item.

Save report to `docs/audits/YYYY-MM-DD-reflect-{N}.md` if any action-item exists.

## Examples

```
Invoke cortex-post-reflection before merge.
```
