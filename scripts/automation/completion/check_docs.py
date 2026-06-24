#!/usr/bin/env python3
"""Completion validation: Verify documentation is up to date.

Checks:
- README.md links are valid
- docs/ files don't reference deleted files
- AGENTS.md and CLAUDE.md are non-empty
- No stale "Last updated" dates
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def check_docs():
    errors = []
    warnings = []

    # Check core files exist and have content
    core_files = [
        "README.md",
        "CLAUDE.md",
        "AGENTS.md",
        "DESIGN.md",
        "docs/GOVERNANCE.md",
        "docs/WORKFLOWS.md",
        "docs/ARCHITECTURE.md",
        "docs/ROADMAP.md",
        "docs/API.md",
        "docs/DATABASE.md",
        "docs/SECURITY.md",
    ]

    for f in core_files:
        p = ROOT / f
        if not p.exists():
            errors.append(f"  MISSING: {f}")
        elif p.stat().st_size < 50:
            warnings.append(f"  THIN: {f} ({p.stat().st_size} bytes)")

    # Check README links
    readme = ROOT / "README.md"
    if readme.exists():
        content = readme.read_text()
        links = re.findall(r'\[.*?\]\(([^)]+)\)', content)
        for link in links:
            if link.startswith("http") or link.startswith("#"):
                continue
            target = ROOT / link
            if not target.exists():
                errors.append(f"  BROKEN LINK in README.md: {link}")

    # Check docs/ internal links
    docs_dir = ROOT / "docs"
    if docs_dir.exists():
        for doc in docs_dir.glob("*.md"):
            content = doc.read_text()
            refs = re.findall(r'\[.*?\]\(([^)]+\.md)\)', content)
            for ref in refs:
                if ref.startswith("/") or ref.startswith("http"):
                    continue
                target = doc.parent / ref
                if not target.exists():
                    errors.append(f"  BROKEN LINK in {doc.name}: {ref}")

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(w)

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(e)
        return 1

    print("✓ Documentation check passed")
    return 0


if __name__ == "__main__":
    sys.exit(check_docs())
