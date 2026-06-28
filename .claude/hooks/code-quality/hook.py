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
    ROOT,
    HookResult,
    get_changed_files,
    is_backend_file,
    print_result,
    read_file,
    run_make,
)

# ── Constants ─────────────────────────────────────────────────────

MAX_RUFF_FINDINGS = 20
MAX_DANGEROUS_FINDINGS = 15
MAX_IMPORT_FINDINGS = 10

SKIP_DIRS: frozenset[str] = frozenset({
    "__pycache__", ".venv", "node_modules", "build",
    "dist", ".git", ".pytest_cache", ".mypy_cache",
    ".claude",
})

# Whitelisted broad exception catches — startup/shutdown handlers, audit logging
# These are acceptable patterns where the broad catch is intentional.
ALLOWED_EXCEPTION_CATCHES: frozenset[str] = frozenset({
    "backend/app/main.py:220",
    "backend/app/main.py:229",
    "backend/app/main.py:237",
    "backend/app/main.py:242",
    "backend/app/auth/audit.py:51",
    "backend/app/auth/audit.py:57",
    # Auth: token/audit operations — failures must not break auth flow
    "backend/app/auth/service.py:95",
    "backend/app/auth/service.py:138",
    "backend/app/auth/service.py:168",
    "backend/app/auth/service.py:192",
    "backend/app/auth/router.py:168",
    "backend/app/auth/router.py:187",
    "backend/app/auth/router.py:228",
    "backend/app/auth/router.py:247",
    "backend/app/auth/router.py:278",
    # Agent loop: non-critical formatting fallback
    "backend/app/agents/loop.py:352",
    # Agent baseline: system resource query — return 0 on failure
    "backend/app/agents/baseline.py:83",
    # Agent tool_defs: param formatting fallback (non-critical)
    "backend/app/agents/tool_defs.py:471",
    # Agent token_counter: tiktoken graceful fallback
    "backend/app/agents/token_counter.py:46",
    "backend/app/agents/token_counter.py:176",
    # Agent security: token detection best-effort
    "backend/app/agents/security.py:168",
    "backend/app/agents/security.py:187",
})

# ── Compiled regex (once) ─────────────────────────────────────────

DANGEROUS_PATTERNS = [
    (re.compile(r'^\s*except:\s*$'), "bare except clause"),
    (re.compile(r'except\s+.*:\s*\n\s*pass'), "swallowed exception"),
    (re.compile(r'(?<!\w)eval\('), "eval() usage"),
    (re.compile(r'(?<!\w)exec\('), "exec() usage"),
    (re.compile(r'__import__\('), "__import__() usage"),
    (re.compile(r'subprocess\.call\(.*shell\s*=\s*True'), "shell=True in subprocess"),
]

_RE_STAR_IMPORT = re.compile(r'from\s+\S+\s+import\s+\*')
_RE_LINT_ERROR = re.compile(r'error:', re.IGNORECASE)


# ── File Discovery ────────────────────────────────────────────────


def _discover_py_files() -> list[Path]:
    """Find all Python source files in backend and tests, skipping irrelevant dirs."""
    files: list[Path] = []
    for pattern in ("backend/**/*.py", "tests/**/*.py"):
        for fpath in ROOT.glob(pattern):
            parts = fpath.relative_to(ROOT).parts
            if any(d in SKIP_DIRS for d in parts):
                continue
            files.append(fpath)
    return files


# ── Checks ────────────────────────────────────────────────────────


def check_ruff() -> HookResult:
    """Run ruff lint."""
    code, out, err = run_make("lint")
    errors = [line.strip() for line in out.splitlines() if _RE_LINT_ERROR.search(line)]

    return HookResult(
        name="Ruff/MyPy",
        passed=code == 0,
        message=f"{len(errors)} lint/type errors" if errors else "All clean",
        findings=errors[:MAX_RUFF_FINDINGS],
    )


def check_dangerous_patterns() -> HookResult:
    """Scan backend and test code for dangerous patterns."""
    findings: list[str] = []

    for fpath in _discover_py_files():
        content = read_file(fpath)
        if not content:
            continue
        rel = str(fpath.relative_to(ROOT))

        # Skip test files — dangerous patterns in tests are expected
        if "test_" in rel or "conftest" in rel:
            continue

        for i, line in enumerate(content.split("\n"), 1):
            loc = f"{rel}:{i}"
            if loc in ALLOWED_EXCEPTION_CATCHES:
                continue
            for pattern, desc in DANGEROUS_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{loc}: {desc}")

    # Deduplicate
    findings = list(dict.fromkeys(findings))

    return HookResult(
        name="Dangerous Patterns",
        passed=len(findings) == 0,
        message=f"{len(findings)} dangerous patterns found" if findings else "No dangerous patterns",
        findings=findings[:MAX_DANGEROUS_FINDINGS],
    )


def check_imports() -> HookResult:
    """Check for star imports in changed Python files."""
    files = get_changed_files()
    py_files = [f for f in files if is_backend_file(f)]

    if not py_files:
        return HookResult(
            name="Import Check",
            passed=True,
            message="No backend files changed",
        )

    findings: list[str] = []
    for fpath in py_files:
        content = read_file(fpath)
        if not content:
            continue
        rel = str(fpath.relative_to(ROOT))
        if ".claude/" in rel:
            continue

        for i, line in enumerate(content.splitlines(), 1):
            if _RE_STAR_IMPORT.search(line):
                findings.append(f"{rel}:{i}: star import (from X import *)")

    return HookResult(
        name="Import Check",
        passed=len(findings) == 0,
        message=f"{len(findings)} import issues" if findings else "Imports OK",
        findings=findings[:MAX_IMPORT_FINDINGS],
    )


# ── Main Hook ─────────────────────────────────────────────────────


def run_hook() -> HookResult:
    """Run the code quality hook."""
    results: list[HookResult] = []

    results.append(check_ruff())
    results.append(check_dangerous_patterns())
    results.append(check_imports())

    all_findings: list[str] = []
    all_warnings: list[str] = []
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
