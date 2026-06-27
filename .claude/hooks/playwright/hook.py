#!/usr/bin/env python3
"""Hook 7 — Playwright Validation Hook (stub)

Trigger: Frontend changes, workflow changes
Purpose: Run Playwright tests for visual/functional validation

NOTE: Playwright is not currently installed in this project.
This hook validates that Playwright config exists and provides
a framework for when it is added.

Currently runs: frontend build check + vitest instead.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, print_result, run_command


def check_playwright_config() -> bool:
    """Check if Playwright is configured."""
    config = ROOT / "frontend" / "playwright.config.ts"
    return config.exists()


def run_vitest() -> HookResult:
    """Run frontend vitest as fallback."""
    code, out, err = run_command(
        ["npm", "test"],
        cwd=ROOT / "frontend",
        timeout=120,
    )
    errors = []
    for line in out.splitlines():
        if "FAIL" in line or "✗" in line or "×" in line:
            errors.append(line.strip())

    return HookResult(
        name="Vitest",
        passed=code == 0,
        message=f"{len(errors)} test failures" if errors else "All frontend tests pass",
        findings=errors[:10],
    )


def run_build_check() -> HookResult:
    """Check frontend build succeeds."""
    code, out, err = run_command(
        ["npm", "run", "build"],
        cwd=ROOT / "frontend",
        timeout=120,
    )
    if code != 0:
        errors = [line.strip() for line in err.splitlines() if "Error" in line or "error" in line]
        return HookResult(
            name="Frontend Build",
            passed=False,
            message="Build failed",
            findings=errors[:10],
        )
    return HookResult(
        name="Frontend Build",
        passed=True,
        message="Build succeeds",
    )


def run_hook() -> HookResult:
    """Run the playwright/build validation hook."""
    has_playwright = check_playwright_config()

    results = []
    results.append(run_vitest())
    results.append(run_build_check())

    if has_playwright:
        # TODO: Add Playwright test runner here
        pass

    all_findings = []
    passed = all(r.passed for r in results)
    for r in results:
        all_findings.extend(r.findings)

    pw_status = "Playwright not configured" if not has_playwright else "Playwright configured"
    return HookResult(
        name="Frontend Validation",
        passed=passed,
        message=f"{pw_status}; " + "; ".join(f"{r.name}: {'✓' if r.passed else '✗'}" for r in results),
        findings=all_findings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
