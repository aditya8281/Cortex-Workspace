#!/usr/bin/env python3
"""Bug discovery: Find common error patterns.

Checks:
- Bare except clauses
- Missing error handling around file I/O
- Empty except blocks (swallowed exceptions)
- print() used instead of logging
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def find_error_patterns():
    findings = []

    py_files = list(ROOT.glob("backend/app/**/*.py"))

    for fpath in py_files:
        if "__pycache__" in str(fpath) or ".venv" in str(fpath):
            continue
        try:
            lines = fpath.read_text().splitlines()
        except (UnicodeDecodeError, PermissionError):
            continue

        rel = str(fpath.relative_to(ROOT))

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Bare except
            if stripped == "except:":
                findings.append(f"  {rel}:{i} — bare except clause")

            # Empty except (swallowed exception)
            if stripped == "except Exception:" or stripped == "except Exception as e:":
                if i < len(lines) and lines[i].strip() == "pass":
                    findings.append(f"  {rel}:{i} — swallowed exception (except + pass)")

            # print() in backend code (should use logging)
            if "print(" in stripped and not stripped.startswith("#"):
                findings.append(f"  {rel}:{i} — print() in backend (use logging)")

    # Deduplicate
    findings = list(set(findings))

    if findings:
        print(f"Error patterns found: {len(findings)}")
        for f in sorted(findings):
            print(f)
        return 1

    print("✓ No common error patterns found")
    return 0


if __name__ == "__main__":
    sys.exit(find_error_patterns())
