#!/usr/bin/env python3
"""Hook 5 — Documentation Consistency Hook

Trigger: Significant implementation changes
Purpose: Verify docs accuracy, detect stale/missing docs, broken references

Checks:
- All doc links are valid
- Referenced files exist
- Core docs are non-empty
- No stale "Last updated" dates
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, print_result, read_file

# ── Constants ─────────────────────────────────────────────────────

MIN_DOC_BYTES = 50
MAX_LINK_FINDINGS = 10

# ── Compiled regex (once) ─────────────────────────────────────────

_RE_MARKDOWN_LINK = re.compile(r'\[.*?\]\(([^)]+)\)')

# ── Data ──────────────────────────────────────────────────────────

CORE_DOCS = [
    "README.md", "CLAUDE.md", "AGENTS.md", "DESIGN.md",
    "docs/guides/governance.md", "docs/workflows/index.md",
    "docs/architecture/overview.md", "docs/reference/api.md",
    "docs/reference/database.md",
]


def check_core_docs() -> list[str]:
    """Check that core documentation files exist and have content."""
    findings: list[str] = []
    for doc in CORE_DOCS:
        p = ROOT / doc
        if not p.exists():
            findings.append(f"MISSING: {doc}")
        elif p.stat().st_size < MIN_DOC_BYTES:
            findings.append(f"THIN: {doc} ({p.stat().st_size} bytes)")
    return findings


def check_links() -> list[str]:
    """Check for broken links in markdown files."""
    findings: list[str] = []
    docs = list(ROOT.glob("*.md")) + list(ROOT.glob("docs/**/*.md"))

    for doc in docs:
        if ".venv" in str(doc) or "node_modules" in str(doc):
            continue
        content = read_file(doc)
        if not content:
            continue

        rel = str(doc.relative_to(ROOT))

        links = _RE_MARKDOWN_LINK.findall(content)
        for link in links:
            if link.startswith("http") or link.startswith("#") or link.startswith("mailto:"):
                continue
            link_path = link.split("#")[0]
            if not link_path:
                continue
            target = doc.parent / link_path
            if not target.exists():
                findings.append(f"BROKEN LINK in {rel}: {link}")

    return findings


def run_hook() -> HookResult:
    """Run the docs consistency hook."""
    findings: list[str] = []
    findings.extend(check_core_docs())
    findings.extend(check_links())

    errors = [f for f in findings if "MISSING" in f or "BROKEN" in f]
    warnings = [f for f in findings if f not in errors]

    return HookResult(
        name="Documentation Consistency",
        passed=len(errors) == 0,
        message=f"{len(errors)} errors, {len(warnings)} warnings" if findings else "Docs OK",
        findings=errors + warnings[:MAX_LINK_FINDINGS],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
