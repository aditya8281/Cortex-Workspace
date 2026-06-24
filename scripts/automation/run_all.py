#!/usr/bin/env python3
"""Master runner: Execute all automation checks.

Usage:
    python scripts/automation/run_all.py              # Run all checks
    python scripts/automation/run_all.py pre-work     # Pre-work checks only
    python scripts/automation/run_all.py development  # Development checks only
    python scripts/automation/run_all.py health       # Health checks only
    python scripts/automation/run_all.py bug-discovery # Bug discovery only
    python scripts/automation/run_all.py completion   # Completion checks only
    python scripts/automation run_all.py report       # Generate full report
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "automation"

PHASES = {
    "pre-work": [
        ("Context", "pre_work/check_context.py"),
        ("Plan", "pre_work/check_plan.py"),
        ("Architecture", "pre_work/check_architecture.py"),
    ],
    "development": [
        ("Contract", "development/check_contract.py"),
        ("Schema", "development/check_schema.py"),
        ("API", "development/check_api.py"),
        ("Types", "development/check_types.py"),
    ],
    "health": [
        ("Dead Code", "health/check_dead_code.py"),
        ("Duplicates", "health/check_duplicate_code.py"),
        ("Dependencies", "health/check_dependencies.py"),
        ("Drift", "health/check_drift.py"),
    ],
    "bug-discovery": [
        ("Placeholders", "bug_discovery/find_placeholders.py"),
        ("Security", "bug_discovery/check_security.py"),
        ("Errors", "bug_discovery/find_errors.py"),
    ],
    "completion": [
        ("Tests", "completion/check_tests.py"),
        ("Docs", "completion/check_docs.py"),
        ("Full validation", "completion/validate_all.py"),
    ],
}


def run_phase(phase_name, checks):
    print(f"\n{'='*50}")
    print(f"  {phase_name.upper()}")
    print(f"{'='*50}")

    failed = 0
    for label, script_rel in checks:
        script = SCRIPTS / script_rel
        if not script.exists():
            print(f"  ○ {label} (script not found)")
            continue
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        icon = "✓" if result.returncode == 0 else "✗"
        print(f"  {icon} {label}")
        if result.returncode != 0:
            failed += 1
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines()[-3:]:
                    print(f"    {line}")

    return failed


def main():
    phase_filter = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print("  CORTEX AUTOMATION FRAMEWORK")
    print("=" * 60)

    total_failed = 0

    if phase_filter:
        if phase_filter == "report":
            # Run report generator
            report_script = SCRIPTS / "reports" / "health_report.py"
            if report_script.exists():
                result = subprocess.run(
                    [sys.executable, str(report_script)],
                    cwd=str(ROOT),
                )
                return result.returncode
            print("Report script not found")
            return 1
        elif phase_filter in PHASES:
            total_failed += run_phase(phase_filter, PHASES[phase_filter])
        else:
            print(f"Unknown phase: {phase_filter}")
            print(f"Valid phases: {', '.join(PHASES.keys())}, report")
            return 1
    else:
        for phase_name, checks in PHASES.items():
            total_failed += run_phase(phase_name, checks)

    print(f"\n{'='*60}")
    if total_failed > 0:
        print(f"  ✗ {total_failed} phase(s) had failures")
    else:
        print("  ✓ All phases passed")
    print("=" * 60)

    return 1 if total_failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
