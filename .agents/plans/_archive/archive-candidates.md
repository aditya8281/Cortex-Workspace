# Archive Candidates

> **This is a recommendation list only — DO NOT delete any files.**
> Files marked below are safe to archive once their content has been verified
> as captured in the active documents listed in each table.

**20 files recommended for archival across 3 categories.**

---

## Category 1: Superseded Planning Documents

Original phase plans and guides that have been replaced by the versioned
planning structure (`versions/v1/` through `versions/v6/`) and `guide.md`.

| # | File | Reason | Superseded By |
|---|------|--------|---------------|
| 1 | `.agents/plans/00-INDEX.md` | Old index | `guide.md` + `versions/` structure |
| 2 | `.agents/plans/01-PHASE-1-FOUNDATION.md` | Original phase plan | `versions/v1/Phase-1.md` |
| 3 | `.agents/plans/02-PHASE-2-AGENT.md` | Original phase plan | `versions/v1/Phase-2.md` |
| 4 | `.agents/plans/03-PHASE-3-MEMORY.md` | Original phase plan | `versions/v2/Phase-3.md` |
| 5 | `.agents/plans/04-PHASE-4-DESKTOP.md` | Original phase plan | `versions/v3/Phase-1.md` |
| 6 | `.agents/plans/05-PHASE-5-DAILY.md` | Original phase plan | `versions/v5/Phase-1.md` |
| 7 | `.agents/plans/06-PHASE-6-PRODUCTION.md` | Original phase plan | `versions/v6/Phase-3.md` |
| 8 | `.agents/plans/07-ARCHITECTURE.md` | Architecture doc | `guide.md` |
| 9 | `.agents/plans/08-PRODUCTION-READINESS.md` | Production readiness | `versions/v6/Phase-3.md` |

**Total: 9 files**

---

## Category 2: Council Discovery Documents

One-time discovery documents produced by the Architecture Council.
Their findings have been absorbed into `guide.md`, `FinalCompatibilities.md`,
`Audit.md`, and the version plans.

| # | File | Reason | Findings Captured In |
|---|------|--------|---------------------|
| 10 | `.agents/plans/council/architecture-decisions.md` | Discovery doc | `guide.md` §4 |
| 11 | `.agents/plans/council/contradictions.md` | Discovery doc | `guide.md` Appendix |
| 12 | `.agents/plans/council/current-state.md` | Discovery doc | `guide.md`, `Audit.md` |
| 13 | `.agents/plans/council/opportunities.md` | Discovery doc | `versions/*/features.md` |
| 14 | `.agents/plans/council/risks.md` | Discovery doc | `versions/*/Phase-*.md` |
| 15 | `.agents/plans/council/strengths.md` | Discovery doc | `guide.md` Appendix |
| 16 | `.agents/plans/council/weaknesses.md` | Discovery doc | `versions/*/features.md` |

**Total: 7 files**

---

## Category 3: Reference Repo Consolidation

One-time analysis documents from the reference repository consolidation effort.
All 73 mapped gaps are captured in the version plans and `FinalCompatibilities.md`.

| # | File | Reason | Findings Captured In |
|---|------|--------|---------------------|
| 17 | `.agents/plans/CORTEX_REFERENCE_CONSOLIDATION_MASTER_PLAN.md` | Master plan — all gaps mapped | `FinalCompatibilities.md` |
| 18 | `.agents/plans/2026-06-25-desktop-reorientation.md` | Desktop reorientation | `guide.md`, `versions/v3/` |
| 19–27 | `.agents/plans/reference-repo-consolidation/*.md` (9 files) | Reference analysis | Version plans, `guide.md` |

**Total: 11 files** (2 named + 9 in subdirectory)

---

## Files to Keep (Do Not Archive)

These files are **active** and must remain in place.

| File | Role |
|------|------|
| `.agents/plans/guide.md` | **Constitution** — active reference for all planning |
| `.agents/plans/FinalCompatibilities.md` | Active cross-reference matrix |
| `.agents/plans/Audit.md` | Active audit record |
| `.agents/plans/implementation_steps.md` | Active contributor guide |
| `.agents/plans/ODYSSEUS_INTEGRATION_PLAN.md` | Active reference — original integration source |
| `.agents/plans/versions/frontend-redesign-evolution.md` | Active design evolution doc |
| `.agents/plans/versions/v1/` through `versions/v6/` | Active implementation plans |

---

## How to Archive

When ready, archive using `git mv` to preserve history:

```bash
# Create archive directory
mkdir -p .agents/plans/_archive

# Category 1: Superseded planning documents
git mv .agents/plans/00-INDEX.md .agents/plans/_archive/
git mv .agents/plans/01-PHASE-1-FOUNDATION.md .agents/plans/_archive/
git mv .agents/plans/02-PHASE-2-AGENT.md .agents/plans/_archive/
git mv .agents/plans/03-PHASE-3-MEMORY.md .agents/plans/_archive/
git mv .agents/plans/04-PHASE-4-DESKTOP.md .agents/plans/_archive/
git mv .agents/plans/05-PHASE-5-DAILY.md .agents/plans/_archive/
git mv .agents/plans/06-PHASE-6-PRODUCTION.md .agents/plans/_archive/
git mv .agents/plans/07-ARCHITECTURE.md .agents/plans/_archive/
git mv .agents/plans/08-PRODUCTION-READINESS.md .agents/plans/_archive/

# Category 2: Council discovery documents
git mv .agents/plans/council/ .agents/plans/_archive/council/

# Category 3: Reference repo consolidation
git mv .agents/plans/CORTEX_REFERENCE_CONSOLIDATION_MASTER_PLAN.md .agents/plans/_archive/
git mv .agents/plans/2026-06-25-desktop-reorientation.md .agents/plans/_archive/
git mv .agents/plans/reference-repo-consolidation/ .agents/plans/_archive/reference-repo-consolidation/
```

Commit the archive move as a single atomic commit:

```bash
git add .agents/plans/_archive/
git commit -m "docs: archive superseded planning docs (20 files, no content changes)"
```
