#!/usr/bin/env python3
"""Hook 10 — Decision Tracking Hook

Trigger: Architecture changes, significant technical decisions
Purpose: Ensure decisions are documented, prevent undocumented architecture changes

Checks:
- ADR exists for architecture changes
- ADR format is correct
- No undocumented new patterns
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, get_changed_files, print_result, read_file

# Files that imply architecture decisions when changed
ARCHITECTURE_INDICATORS = [
    "backend/app/main.py",           # App factory
    "backend/app/core/config.py",     # Configuration
    "backend/app/api/router.py",      # API routing
    "backend/app/db/",                # Database layer
    "migrations/",                    # Schema changes
    "docker-compose.yml",             # Infrastructure
    "pyproject.toml",                 # Dependencies
    ".github/workflows/",             # CI/CD
]

# New files that imply patterns
PATTERN_INDICATORS = {
    "backend/app/services/": "new service",
    "backend/app/middleware/": "new middleware",
    "backend/app/managers/": "new manager",
    "backend/app/tasks/": "new background task",
}


def check_adr_exists() -> list:
    """Check if ADR directory has entries."""
    findings = []
    adr_dir = ROOT / "docs" / "decisions"
    if not adr_dir.exists():
        findings.append("docs/decisions/ directory missing — ADRs should be tracked")
        return findings

    adrs = list(adr_dir.glob("*.md"))
    if not adrs:
        findings.append("No ADRs found in docs/decisions/")
    else:
        # Validate each ADR
        for adr in adrs:
            content = read_file(adr)
            if not content:
                findings.append(f"Empty ADR: {adr.name}")
                continue

            has_status = "**Status:**" in content
            has_date = "**Date:**" in content
            has_context = "## Context" in content
            has_decision = "## Decision" in content
            has_consequences = "## Consequences" in content

            missing = []
            if not has_status: missing.append("Status")
            if not has_date: missing.append("Date")
            if not has_context: missing.append("Context")
            if not has_decision: missing.append("Decision")
            if not has_consequences: missing.append("Consequences")

            if missing:
                findings.append(f"{adr.name}: missing {', '.join(missing)}")

    return findings


def check_architecture_changes() -> list:
    """Check if architecture-significant files were modified without ADR."""
    findings = []
    changed = get_changed_files()
    changed_strs = [str(f.relative_to(ROOT)) for f in changed]

    arch_changed = any(
        any(indicator in c for indicator in ARCHITECTURE_INDICATORS)
        for c in changed_strs
    )

    if arch_changed:
        adr_dir = ROOT / "docs" / "decisions"
        adrs = list(adr_dir.glob("*.md")) if adr_dir.exists() else []
        if not adrs:
            findings.append("Architecture files modified but no ADR exists")

    # Check for new service/middleware/manager files
    new_pattern_files = []
    for f in changed:
        rel = str(f.relative_to(ROOT))
        for pattern, desc in PATTERN_INDICATORS.items():
            if rel.startswith(pattern) and f.exists():
                content = read_file(f)
                if content and len(content) > 100:  # Non-trivial file
                    new_pattern_files.append(f"{desc}: {rel}")

    if new_pattern_files:
        findings.append(f"New patterns introduced (consider ADR): {', '.join(new_pattern_files)}")

    return findings


def run_hook() -> HookResult:
    """Run the decision tracking hook."""
    findings = []
    findings.extend(check_adr_exists())
    findings.extend(check_architecture_changes())

    errors = [f for f in findings if "missing" in f.lower() and "ADR" in f]
    warnings = [f for f in findings if f not in errors]

    return HookResult(
        name="Decision Tracking",
        passed=len(errors) == 0,
        message=f"{len(errors)} issues, {len(warnings)} warnings" if findings else "Decisions tracked",
        findings=errors + warnings[:10],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
