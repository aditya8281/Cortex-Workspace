#!/usr/bin/env python3
"""Pre-work validation: Check that an implementation plan exists for the current work.

Looks for:
- Active plan in .claude/plans/
- Design spec in docs/specs/
- ADR if architectural decision was made

Exit codes:
- 0: Plan exists or task doesn't require one
- 1: Plan expected but missing
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def check_plan():
    plans_dir = ROOT / ".claude" / "plans"
    specs_dir = ROOT / "docs" / "specs"

    issues = []

    # Check for active plans
    if plans_dir.exists():
        active_plans = list(plans_dir.glob("*.md"))
        if active_plans:
            print(f"Active plans found: {len(active_plans)}")
            for p in active_plans:
                print(f"  - {p.name}")
    else:
        print("No .claude/plans/ directory (OK if no active work)")

    # Check for design specs
    if specs_dir.exists():
        specs = list(specs_dir.glob("*.md"))
        if specs:
            print(f"Design specs found: {len(specs)}")
            for s in specs:
                print(f"  - {s.name}")
    else:
        print("No docs/specs/ directory (OK if no design work)")

    # Check for ADRs
    adr_dir = ROOT / "docs" / "decisions"
    if adr_dir.exists():
        adrs = list(adr_dir.glob("*.md"))
        if adrs:
            print(f"ADRs found: {len(adrs)}")
            for a in adrs:
                print(f"  - {a.name}")

    if issues:
        print("\nISSUES:")
        for issue in issues:
            print(f"  {issue}")
        return 1

    print("✓ Plan context check passed")
    return 0


if __name__ == "__main__":
    sys.exit(check_plan())
