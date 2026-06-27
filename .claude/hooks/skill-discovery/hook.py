#!/usr/bin/env python3
"""Hook — Skill Discovery Reminder

Trigger: Any significant task
Purpose: Remind agents to search for skills before implementing

This hook checks:
- Whether skills were considered (informational, not blocking)
- Whether a workflow could become a skill (gap detection)
- Whether existing skills are up to date (staleness check)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, print_result


def check_skill_inventory() -> list:
    """List available skills and their status."""
    findings = []
    skills_dir = ROOT / ".agents" / "skills"
    if not skills_dir.exists():
        return ["No .claude/skills/ directory found"]

    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]

    # Check for skill definitions
    for skill_dir in skill_dirs:
        # Look for skill definition files
        has_definition = False
        for f in skill_dir.iterdir():
            if f.suffix in (".md", ".txt", ".yaml", ".yml", ".json", ".py"):
                has_definition = True
                break

        if not has_definition:
            findings.append(f"Skill '{skill_dir.name}' has no definition file")

    return findings


def check_hook_coverage() -> list:
    """Check if hooks cover all workflow phases."""
    findings = []
    hooks_dir = ROOT / ".claude" / "hooks"
    if not hooks_dir.exists():
        return []

    hook_dirs = [d.name for d in hooks_dir.iterdir() if d.is_dir() and not d.name.startswith(("_", "shared"))]

    # Expected hooks (from governance)
    expected = [
        "ui-review", "code-quality", "contract", "architecture",
        "docs-consistency", "planning", "playwright", "completion-gate",
        "repo-health", "decision-tracking",
    ]

    missing = [h for h in expected if h not in hook_dirs]
    if missing:
        for h in missing:
            findings.append(f"Missing hook: {h}")

    extra = [h for h in hook_dirs if h not in expected and h != "skill-discovery"]
    if extra:
        for h in extra:
            findings.append(f"Unregistered hook: {h} (add to run_hooks.py)")

    return findings


def check_automation_coverage() -> list:
    """Check if automation scripts cover all phases."""
    findings = []
    auto_dir = ROOT / "scripts" / "automation"
    if not auto_dir.exists():
        return []

    phases = [d.name for d in auto_dir.iterdir() if d.is_dir() and not d.name.startswith("__")]

    expected = ["pre_work", "development", "health", "bug_discovery", "completion", "reports"]
    missing = [p for p in expected if p not in phases]

    if missing:
        for p in missing:
            findings.append(f"Missing automation phase: {p}")

    return findings


def run_hook():
    """Run the skill discovery hook."""
    findings = []
    findings.extend(check_skill_inventory())
    findings.extend(check_hook_coverage())
    findings.extend(check_automation_coverage())

    errors = [f for f in findings if "Missing" in f]
    warnings = [f for f in findings if f not in errors]

    return HookResult(
        name="Skill Discovery",
        passed=True,  # Informational, not blocking
        message=f"{len(errors)} missing, {len(warnings)} warnings" if findings else "Ecosystem complete",
        findings=findings[:10],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
