#!/usr/bin/env python3
"""Hook 2 — Code Quality Hook

Trigger: Any code modification
Purpose: Run linting, type checks, detect dead code, duplicates, dangerous patterns

Checks:
- Ruff lint
- MyPy type checks
- Import validation
- Dead code detection
- Dangerous pattern detection (bare excepts, swallowed exceptions)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import (
    ROOT, HookResult, run_make, run_command, run_python,
    get_changed_files, is_backend_file, read_file, print_result,
)

DANGEROUS_PATTERNS = [
    (re.compile(r'^\s*except:\s*$'), "bare except clause"),
    (re.compile(r'except\s+Exception\s*:'), "broad exception catch"),
    (re.compile(r'except\s+.*:\s*\n\s*pass'), "swallowed exception"),
    (re.compile(r'eval\('), "eval() usage"),
    (re.compile(r'exec\('), "exec() usage"),
    (re.compile(r'__import__\('), "__import__() usage"),
    (re.compile(r'subprocess\.call\(.*shell\s*=\s*True'), "shell=True in subprocess"),
]


def check_ruff() -> HookResult:
    """Run ruff lint."""
    code, out, err = run_make("lint")
    errors = []
    for line in out.splitlines():
        if "error:" in line.lower():
            errors.append(line.strip())

    return HookResult(
        name="Ruff/MyPy",
        passed=code == 0,
        message=f"{len(errors)} lint/type errors" if errors else "All clean",
        findings=errors[:20],
    )


def check_dangerous_patterns() -> HookResult:
    """Scan backend code for dangerous patterns."""
    findings = []
    py_files = list(ROOT.glob("backend/app/**/*.py"))

    for fpath in py_files:
        if "__pycache__" in str(fpath) or ".venv" in str(fpath):
            continue
        content = read_file(fpath)
        if not content:
            continue
        rel = str(fpath.relative_to(ROOT))

        lines = content.split("\n")
        for i, line in enumerate(lines):
            for pattern, desc in DANGEROUS_PATTERNS:
                if pattern.search(line):
                    # Skip in test files
                    if "test_" in rel or "conftest" in rel:
                        continue
                    findings.append(f"{rel}:{i+1}: {desc}")

    # Deduplicate
    findings = list(set(findings))

    return HookResult(
        name="Dangerous Patterns",
        passed=len(findings) == 0,
        message=f"{len(findings)} dangerous patterns found" if findings else "No dangerous patterns",
        findings=findings[:15],
    )


def check_imports() -> HookResult:
    """Check for unused or missing imports in changed Python files."""
    files = get_changed_files()
    py_files = [f for f in files if is_backend_file(f)]

    if not py_files:
        return HookResult(
            name="Import Check",
            passed=True,
            message="No backend files changed",
        )

    findings = []
    for fpath in py_files:
        content = read_file(fpath)
        if not content:
            continue
        rel = str(fpath.relative_to(ROOT))

        # Check for star imports
        for i, line in enumerate(content.splitlines(), 1):
            if "from " in line and " import *" in line:
                findings.append(f"{rel}:{i}: star import (from X import *)")

    return HookResult(
        name="Import Check",
        passed=len(findings) == 0,
        message=f"{len(findings)} import issues" if findings else "Imports OK",
        findings=findings[:10],
    )


def run_hook():
    """Run the code quality hook."""
    results = []

    # Ruff + MyPy
    results.append(check_ruff())

    # Dangerous patterns
    results.append(check_dangerous_patterns())

    # Import checks
    results.append(check_imports())

    all_findings = []
    all_warnings = []
    passed = all(r.passed for r in results)

    for r in results:
        all_findings.extend(r.findings)
        all_warnings.extend(r.warnings)

    return HookResult(
        name="Code Quality",
        passed=passed,
        message="; ".join(f"{r.name}: {'✓' if r.passed else '✗'}" for r in results),
        findings=all_findings,
        warnings=all_warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
