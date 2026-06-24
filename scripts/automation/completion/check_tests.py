#!/usr/bin/env python3
"""Completion validation: Verify all tests pass."""

import subprocess
import sys


def check_tests():
    print("Running backend tests...")
    result = subprocess.run(
        ["uv", "run", "pytest", "-v", "--tb=short"],
        capture_output=True, text=True,
        cwd="/home/adi/Desktop/Cortex-Workspace",
    )
    if result.returncode != 0:
        print("Backend tests FAILED:")
        print(result.stdout[-1000:])
        return 1

    # Count passed tests
    passed = result.stdout.count(" PASSED")
    failed = result.stdout.count(" FAILED")
    print(f"Backend: {passed} passed, {failed} failed ✓")
    return 0


if __name__ == "__main__":
    sys.exit(check_tests())
