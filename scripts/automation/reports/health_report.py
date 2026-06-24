#!/usr/bin/env python3
"""Report: Repository health summary.

Runs all health checks and produces a consolidated report.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts" / "automation"

HEALTH_CHECKS = [
    ("Dead Code", "health/check_dead_code.py"),
    ("Duplicate Code", "health/check_duplicate_code.py"),
    ("Dependencies", "health/check_dependencies.py"),
    ("Architecture Drift", "health/check_drift.py"),
    ("Security", "bug_discovery/check_security.py"),
    ("Placeholders", "bug_discovery/find_placeholders.py"),
    ("Error Patterns", "bug_discovery/find_errors.py"),
]


def run_check(label, script_rel):
    script = SCRIPTS / script_rel
    if not script.exists():
        return label, "skip", f"{script_rel} not found"

    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    status = "pass" if result.returncode == 0 else "fail"
    output = result.stdout.strip()
    return label, status, output


def generate_report():
    print("=" * 60)
    print("  CORTEX REPOSITORY HEALTH REPORT")
    print("=" * 60)
    print()

    results = []
    for label, script in HEALTH_CHECKS:
        label, status, output = run_check(label, script)
        results.append((label, status, output))
        icon = "✓" if status == "pass" else "✗" if status == "fail" else "○"
        print(f"  {icon} {label}")

    passed = sum(1 for _, s, _ in results if s == "pass")
    failed = sum(1 for _, s, _ in results if s == "fail")
    skipped = sum(1 for _, s, _ in results if s == "skip")
    total = len(results)

    print()
    print("-" * 60)
    print(f"  Results: {passed}/{total} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        print()
        print("  Failed checks:")
        for label, status, output in results:
            if status == "fail":
                print(f"  --- {label} ---")
                for line in output.splitlines()[:10]:
                    print(f"    {line}")

    print("-" * 60)

    report_path = ROOT / "docs" / "audits"
    if report_path.exists():
        from datetime import date
        report_file = report_path / f"{date.today().isoformat()}-health-report.md"
        with open(report_file, "w") as f:
            f.write(f"# Repository Health Report: {date.today().isoformat()}\n\n")
            f.write(f"| Check | Status |\n|-------|--------|\n")
            for label, status, _ in results:
                icon = "✓" if status == "pass" else "✗" if status == "fail" else "○"
                f.write(f"| {label} | {icon} {status} |\n")
            f.write(f"\n**Summary:** {passed}/{total} passed, {failed} failed, {skipped} skipped\n")
            for label, status, output in results:
                if status == "fail":
                    f.write(f"\n## {label}\n\n```\n{output}\n```\n")
        print(f"\nReport saved: {report_file.relative_to(ROOT)}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(generate_report())
