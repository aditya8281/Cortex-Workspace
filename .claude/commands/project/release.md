# /project:release — Release Readiness Check

Determine if the current state is ready for release of the active version/phase. Combines verification, documentation, governance, and version completeness.

**Scope:** Version/phase release gate. For just test/lint/build results, use `/project:verify` instead.

## Instructions

### 1. Read Version Context

Run `.agents/plans/shared-phases.md#repository-intelligence`.
Run `.agents/plans/shared-phases.md#planning-ecosystem-load`.

Identify the phase exit criteria from the active phase plan.

### 2. Run Verification

Run `.agents/plans/shared-phases.md#system-validation`.

### 3. Check Phase Completeness

For each exit criterion in the phase plan:
- Is it met? (Yes/No)
- What evidence supports this? (test output, code reference, doc reference)

Flag any incomplete items.

### 4. Check Documentation

Run `.agents/plans/shared-phases.md#documentation-consistency-check`.

### 5. Check Governance

| Check | Status |
|-------|--------|
| All hooks passing | ✅/❌ |
| `progress.md` up to date | ✅/❌ |
| No unresolved P0/P1 from code review | ✅/❌ |
| No unresolved P0/P1 from adversarial review | ✅/❌ |

### 6. Check Git State

| Check | Status |
|-------|--------|
| Clean working tree | ✅/❌ |
| Meaningful commit history | ✅/❌ |
| No merge conflicts | ✅/❌ |

### 7. Check Version Boundaries

- Does anything in this release belong in a different version?
- Is scope creep present? (features from V2+ leaking into V1)

## Output

```markdown
## Release Readiness: [date]

### Version: VX — Phase N: [name]

### Verification
[Results from verify checks]

### Phase Completeness
| Criterion | Status | Evidence |
|-----------|--------|----------|

### Documentation
| Check | Status |
|-------|--------|

### Governance
| Check | Status |
|-------|--------|

### Git State
| Check | Status |
|-------|--------|

### Version Boundaries
| Check | Status |
|-------|--------|

### Verdict: READY / NOT READY
### Blockers: [list if any]
```
