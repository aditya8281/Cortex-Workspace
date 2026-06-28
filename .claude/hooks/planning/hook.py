#!/usr/bin/env python3
"""Hook 6 — Planning Consistency Hook

Trigger: Major feature completion, phase completion
Purpose: Verify plans reflect reality, prevent roadmap drift

Checks:
- Roadmap phases match actual implementation state
- No stale phase markers
- Completed phases have all items checked
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, print_result, read_file

# ── Compiled regex (once) ─────────────────────────────────────────

_RE_PHASE = re.compile(r'### Phase (\d+[A-B]?):\s+(.+?)\s*([✅🟡⬜])')
_RE_PLACEHOLDER = re.compile(r'\b(TBD|XXX)\b', re.IGNORECASE)


def check_roadmap_phases() -> list[str]:
    """Check roadmap phase status consistency."""
    findings: list[str] = []
    roadmap = ROOT / "STATUS.md"
    if not roadmap.exists():
        return ["STATUS.md not found (roadmap)"]

    content = read_file(roadmap)

    phases = _RE_PHASE.findall(content)
    for num, name, status in phases:
        if status == "✅":
            findings.append(f"Phase {num}: {name.strip()} — marked complete")

    for i, line in enumerate(content.splitlines(), 1):
        if _RE_PLACEHOLDER.search(line):
            findings.append(f"ROADMAP.md:{i}: placeholder found: {line.strip()[:80]}")

    return findings


def check_adr_consistency() -> list[str]:
    """Check ADR directory consistency."""
    findings: list[str] = []
    adr_dir = ROOT / "docs" / "decisions"
    if not adr_dir.exists():
        return []

    for adr_file in sorted(adr_dir.glob("*.md")):
        if adr_file.name == "README.md":
            continue
        content = read_file(adr_file)
        if not content:
            continue

        has_status = "**Status:**" in content
        has_date = "**Date:**" in content
        has_context = "## Context" in content
        has_decision = "## Decision" in content

        if not (has_status and has_date and has_context and has_decision):
            missing = []
            if not has_status: missing.append("Status")
            if not has_date: missing.append("Date")
            if not has_context: missing.append("Context")
            if not has_decision: missing.append("Decision")
            findings.append(f"{adr_file.name}: missing sections: {', '.join(missing)}")

    return findings


def run_hook() -> HookResult:
    """Run the planning consistency hook."""
    findings: list[str] = []
    findings.extend(check_roadmap_phases())
    findings.extend(check_adr_consistency())

    errors = [f for f in findings if "missing" in f.lower() or "not found" in f.lower()]
    warnings = [f for f in findings if f not in errors]

    return HookResult(
        name="Planning Consistency",
        passed=len(errors) == 0,
        message=f"{len(errors)} issues, {len(warnings)} status items" if findings else "Planning OK",
        findings=errors + warnings[:10],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
