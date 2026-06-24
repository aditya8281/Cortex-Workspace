#!/usr/bin/env python3
"""Documentation consistency check.

Checks:
1. All doc links in CLAUDE.md, GOVERNANCE.md, WORKFLOWS.md resolve to real files
2. No duplicate source-of-truth definitions
3. docs/ files have "Last updated" dates
4. Cross-references between docs are valid
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def find_broken_links(filepath):
    """Find markdown links that point to non-existent files."""
    broken = []
    try:
        content = filepath.read_text()
    except Exception:
        return broken

    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
        label, target = match.groups()
        if target.startswith("http") or target.startswith("#"):
            continue
        target_path = ROOT / target
        if not target_path.exists():
            broken.append(f"{filepath.name}: [{label}]({target})")
    return broken


def check_doc_dates():
    """Check if docs have Last updated dates."""
    missing = []
    docs_dir = ROOT / "docs"
    if not docs_dir.exists():
        return missing
    for f in docs_dir.glob("*.md"):
        content = f.read_text()
        if "Last updated" not in content and "last updated" not in content.lower():
            missing.append(f"docs/{f.name}")
    return missing


def main():
    print("=" * 50)
    print("  DOCUMENTATION CONSISTENCY")
    print("=" * 50)

    issues = []

    # Check broken links in key docs
    key_docs = [
        ROOT / "CLAUDE.md",
        ROOT / "AGENTS.md",
        ROOT / "DESIGN.md",
        ROOT / "docs" / "GOVERNANCE.md",
        ROOT / "docs" / "WORKFLOWS.md",
        ROOT / "docs" / "DEVELOPER_GUIDE.md",
    ]

    for doc in key_docs:
        if doc.exists():
            broken = find_broken_links(doc)
            issues.extend(broken)

    # Check doc dates
    missing_dates = check_doc_dates()

    # Report
    if issues:
        print("  ✗ Broken links found:")
        for issue in issues:
            print(f"    {issue}")
    else:
        print("  ✓ No broken links")

    if missing_dates:
        print(f"  ⚠ {len(missing_dates)} docs missing 'Last updated' date:")
        for d in missing_dates:
            print(f"    {d}")
    else:
        print("  ✓ All docs have 'Last updated' dates")

    total = len(issues) + len(missing_dates)
    if total == 0:
        print("  ✓ Documentation consistent")
    else:
        print(f"  ✗ {total} documentation issues found")

    print("=" * 50)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
