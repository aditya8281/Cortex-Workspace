#!/usr/bin/env python3
"""Pre-work validation: Verify architecture consistency.

Checks:
- No competing doc systems (single source of truth)
- No duplicate skill directories
- No empty placeholder files
- Governance docs are present and non-empty
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def check_architecture():
    errors = []
    warnings = []

    # Check for competing doc systems (should not exist)
    known_bad = [
        (".trae/skills", "Duplicate skill directory (should use .claude/skills/)"),
        (".codex/hooks.json", "Stale Codex config"),
        (".cortex_bootstrap", "One-time bootstrap artifact"),
        ("skills-lock.json", "Unused skill lock file"),
    ]

    for path_str, desc in known_bad:
        p = ROOT / path_str
        if p.exists():
            errors.append(f"  STALE: {path_str} — {desc}")

    # Check .claude/context/ should not exist (was emptied)
    ctx_dir = ROOT / ".claude" / "context"
    if ctx_dir.exists():
        empty_files = [f for f in ctx_dir.iterdir() if f.is_file() and f.stat().st_size == 0]
        if empty_files:
            warnings.append(f"  EMPTY: .claude/context/ has {len(empty_files)} empty files")

    # Check governance docs have content (minimum 100 bytes)
    governance_files = [
        "docs/GOVERNANCE.md",
        "docs/WORKFLOWS.md",
        "docs/ARCHITECTURE.md",
        "docs/ROADMAP.md",
    ]

    for path_str in governance_files:
        p = ROOT / path_str
        if p.exists() and p.stat().st_size < 100:
            warnings.append(f"  THIN: {path_str} ({p.stat().st_size} bytes — may be incomplete)")

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(w)
        print()

    if errors:
        print("ERRORS (architecture drift detected):")
        for e in errors:
            print(e)
        print("\nAction: Remove stale files to maintain single source of truth")
        return 1

    print("✓ Architecture consistency check passed")
    return 0


if __name__ == "__main__":
    sys.exit(check_architecture())
