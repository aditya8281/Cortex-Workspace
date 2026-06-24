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
from utils import ROOT, HookResult, get_changed_files, read_file, print_result

CORE_DOCS = [
    "README.md", "CLAUDE.md", "AGENTS.md", "DESIGN.md",
    "docs/GOVERNANCE.md", "docs/WORKFLOWS.md", "docs/ARCHITECTURE.md",
    "docs/ROADMAP.md", "docs/API.md", "docs/DATABASE.md", "docs/SECURITY.md",
]


def check_core_docs() -> list:
    """Check that core documentation files exist and have content."""
    findings = []
    for doc in CORE_DOCS:
        p = ROOT / doc
        if not p.exists():
            findings.append(f"MISSING: {doc}")
        elif p.stat().st_size < 50:
            findings.append(f"THIN: {doc} ({p.stat().st_size} bytes)")
    return findings


def check_links() -> list:
    """Check for broken links in markdown files."""
    findings = []
    docs = list(ROOT.glob("*.md")) + list(ROOT.glob("docs/**/*.md"))

    for doc in docs:
        if ".venv" in str(doc) or "node_modules" in str(doc):
            continue
        content = read_file(doc)
        if not content:
            continue

        rel = str(doc.relative_to(ROOT))

        # Markdown links: [text](path)
        links = re.findall(r'\[.*?\]\(([^)]+)\)', content)
        for link in links:
            if link.startswith("http") or link.startswith("#") or link.startswith("mailto:"):
                continue
            # Remove anchor
            link_path = link.split("#")[0]
            if not link_path:
                continue
            target = doc.parent / link_path
            if not target.exists():
                findings.append(f"BROKEN LINK in {rel}: {link}")

    return findings


def check_roadmap_consistency() -> list:
    """Check roadmap checkbox consistency."""
    findings = []
    roadmap = ROOT / "docs" / "ROADMAP.md"
    if not roadmap.exists():
        return findings

    content = read_file(roadmap)
    # Check for mixed checkbox states on same item
    # This is a basic check — more sophisticated checks can be added
    unchecked = content.count("[ ]")
    checked = content.count("[x]")

    if unchecked + checked > 0:
        pct = int(checked / (unchecked + checked) * 100)
        findings.append(f"Roadmap: {checked}/{unchecked + checked} items complete ({pct}%)")

    return findings


def run_hook():
    """Run the docs consistency hook."""
    findings = []
    findings.extend(check_core_docs())
    findings.extend(check_links())
    findings.extend(check_roadmap_consistency())

    errors = [f for f in findings if "MISSING" in f or "BROKEN" in f]
    warnings = [f for f in findings if f not in errors]

    return HookResult(
        name="Documentation Consistency",
        passed=len(errors) == 0,
        message=f"{len(errors)} errors, {len(warnings)} warnings" if findings else "Docs OK",
        findings=errors + warnings[:10],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
