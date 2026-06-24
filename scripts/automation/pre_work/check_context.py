#!/usr/bin/env python3
"""Pre-work validation: Check that required context files exist and are populated.

Checks:
- CLAUDE.md exists and has content
- AGENTS.md exists and has content
- docs/GOVERNANCE.md exists
- docs/WORKFLOWS.md exists
- docs/ARCHITECTURE.md exists
- docs/ROADMAP.md exists
- .claude/settings.local.json exists
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

REQUIRED_FILES = [
    ("CLAUDE.md", "Agent guidance document"),
    ("AGENTS.md", "Agent behavior rules"),
    ("docs/GOVERNANCE.md", "Governance rules"),
    ("docs/WORKFLOWS.md", "Workflow definitions"),
    ("docs/ARCHITECTURE.md", "Architecture reference"),
    ("docs/ROADMAP.md", "Development roadmap"),
    (".claude/settings.local.json", "Claude Code settings"),
]

OPTIONAL_FILES = [
    ("DESIGN.md", "Frontend design system"),
    ("docs/API.md", "API reference"),
    ("docs/DATABASE.md", "Database schema reference"),
    ("docs/SECURITY.md", "Security patterns"),
]


def check_context():
    errors = []
    warnings = []

    for path_str, desc in REQUIRED_FILES:
        p = ROOT / path_str
        if not p.exists():
            errors.append(f"  MISSING: {path_str} ({desc})")
        elif p.stat().st_size == 0:
            errors.append(f"  EMPTY:   {path_str} ({desc})")

    for path_str, desc in OPTIONAL_FILES:
        p = ROOT / path_str
        if not p.exists():
            warnings.append(f"  MISSING: {path_str} ({desc})")
        elif p.stat().st_size == 0:
            warnings.append(f"  EMPTY:   {path_str} ({desc})")

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(w)
        print()

    if errors:
        print("ERRORS (required files missing or empty):")
        for e in errors:
            print(e)
        print()
        print("Run: make ecosystem-init  to fix")
        return 1

    print("✓ All required context files present and populated")
    return 0


if __name__ == "__main__":
    sys.exit(check_context())
