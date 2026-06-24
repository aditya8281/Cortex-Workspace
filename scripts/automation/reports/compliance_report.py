#!/usr/bin/env python3
"""Report: Governance and workflow compliance.

Checks adherence to ecosystem rules defined in CLAUDE.md and AGENTS.md.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts" / "automation"


def run_check(label, script_rel):
    script = SCRIPTS / script_rel
    if not script.exists():
        return label, "skip"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    status = "pass" if result.returncode == 0 else "fail"
    return label, status


def generate_report():
    print("=" * 60)
    print("  CORTEX GOVERNANCE COMPLIANCE REPORT")
    print("=" * 60)
    print()

    checks = [
        ("Context files exist", "pre_work/check_context.py"),
        ("Architecture consistent", "pre_work/check_architecture.py"),
        ("API conventions", "development/check_api.py"),
        ("Schema consistent", "development/check_schema.py"),
        ("No hardcoded secrets", "bug_discovery/check_security.py"),
        ("Documentation valid", "completion/check_docs.py"),
    ]

    results = []
    for label, script in checks:
        label, status = run_check(label, script)
        results.append((label, status))
        icon = "✓" if status == "pass" else "✗" if status == "fail" else "○"
        print(f"  {icon} {label}")

    passed = sum(1 for _, s in results if s == "pass")
    total = len(results)

    print()
    print("-" * 60)
    print(f"  Compliance: {passed}/{total} checks passed")

    if passed < total:
        print(f"\n  Non-compliant checks:")
        for label, status in results:
            if status == "fail":
                print(f"    ✗ {label}")

    print("-" * 60)
    return 1 if passed < total else 0


if __name__ == "__main__":
    sys.exit(generate_report())
