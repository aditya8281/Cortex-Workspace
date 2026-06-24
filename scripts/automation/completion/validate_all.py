#!/usr/bin/env python3
"""Completion validation: Run all checks before merge/push.

Checks: lint, tests, build, schema, API conventions.
"""

import subprocess
import sys


def run_check(label, cmd):
    print(f"--- {label} ---")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="/home/adi/Desktop/Cortex-Workspace")
    if result.returncode == 0:
        print(f"  ✓ {label} passed")
        return True
    else:
        print(f"  ✗ {label} failed")
        if result.stdout.strip():
            print(result.stdout[-500:])
        return True if result.returncode == 0 else False


def validate_all():
    results = []

    results.append(("ruff lint", run_check("ruff lint", ["uv", "run", "ruff", "check", "backend/", "tests/"])))
    results.append(("mypy", run_check("mypy", ["uv", "run", "mypy", "backend/", "--ignore-missing-imports", "--explicit-package-bases", "--implicit-optional"])))
    results.append(("pytest", run_check("pytest", ["uv", "run", "pytest", "-v", "--tb=short"])))
    results.append(("contract check", run_check("contract check", ["python", "scripts/automation/development/check_contract.py"])))
    results.append(("schema check", run_check("schema check", ["python", "scripts/automation/development/check_schema.py"])))
    results.append(("api check", run_check("api conventions", ["python", "scripts/automation/development/check_api.py"])))

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed")
    for label, ok in results:
        print(f"  {'✓' if ok else '✗'} {label}")

    if passed < total:
        print(f"\n{total - passed} check(s) failed — fix before pushing")
        return 1

    print("\n✓ All completion checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(validate_all())
