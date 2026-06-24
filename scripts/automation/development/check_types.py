#!/usr/bin/env python3
"""Development validation: Type checking via mypy.

Wraps `make lint` but focuses on type-checking output.
"""

import subprocess
import sys


def check_types():
    print("Running mypy type check...")
    result = subprocess.run(
        ["make", "lint"],
        capture_output=True,
        text=True,
        cwd="/home/adi/Desktop/Cortex-Workspace",
    )

    if result.returncode == 0:
        print("✓ Type check passed")
        return 0

    print("Type check failed:")
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(check_types())
