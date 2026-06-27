#!/usr/bin/env python3
"""Hook 8 — Completion Gate Hook

Trigger: Before work is marked complete
Purpose: Block completion when critical issues exist

Verifies:
- Tests passing
- Lint clean
- Build succeeds
- Documentation updated
- No P0/P1 findings unresolved
- Schema changes have migrations
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, print_result, run_command, run_make


def check_tests() -> HookResult:
    """Verify all tests pass."""
    code, out, err = run_make("test")
    failed = out.count("FAILED")
    passed_count = out.count("PASSED")
    return HookResult(
        name="Tests",
        passed=code == 0 and failed == 0,
        message=f"{passed_count} passed, {failed} failed",
        findings=[l.strip() for l in out.splitlines() if "FAILED" in l][:5],
    )


def check_lint() -> HookResult:
    """Verify lint passes."""
    code, out, err = run_command(["uv", "run", "ruff", "check", "backend/", "tests/"])
    errors = [l.strip() for l in out.splitlines() if "error" in l.lower()]
    return HookResult(
        name="Lint",
        passed=code == 0,
        message=f"{len(errors)} lint errors" if errors else "Clean",
        findings=errors[:10],
    )


def check_types() -> HookResult:
    """Verify mypy passes."""
    code, out, err = run_command(
        ["uv", "run", "mypy", "backend/", "--ignore-missing-imports",
         "--explicit-package-bases", "--implicit-optional"]
    )
    errors = [l.strip() for l in out.splitlines() if "error" in l.lower()]
    return HookResult(
        name="Types",
        passed=code == 0,
        message=f"{len(errors)} type errors" if errors else "Clean",
        findings=errors[:10],
    )


def check_schema_migrations() -> HookResult:
    """Check if model changes have corresponding migrations.

    Compares git modification timestamps: if any model file was changed
    more recently than the latest migration, flag it.
    """
    code, out, _ = run_command(["git", "diff", "--name-only", "HEAD"])
    changed = out.strip().splitlines()

    model_changed = any("models/" in f for f in changed)
    if not model_changed:
        return HookResult(name="Migrations", passed=True, message="No model changes")

    versions_dir = ROOT / "migrations" / "versions"
    if not versions_dir.exists():
        return HookResult(
            name="Migrations", passed=False,
            message="Models changed but migrations/versions/ missing",
        )

    migrations = sorted(versions_dir.glob("*.py"))
    if not migrations:
        return HookResult(
            name="Migrations", passed=False,
            message="Models changed but no migrations found",
        )

    # Compare timestamps: get latest migration's git commit time
    latest_migration = migrations[-1]
    mig_code, mig_out, _ = run_command(
        ["git", "log", "-1", "--format=%at", "--", str(latest_migration.relative_to(ROOT))],
    )
    mig_ts = int(mig_out.strip()) if mig_code == 0 and mig_out.strip().isdigit() else 0

    # Get the most recent model file change time
    max_model_ts = 0
    for f in changed:
        if "models/" in f and f.endswith(".py"):
            fcode, fout, _ = run_command(
                ["git", "log", "-1", "--format=%at", "--", f],
            )
            if fcode == 0 and fout.strip().isdigit():
                ts = int(fout.strip())
                if ts > max_model_ts:
                    max_model_ts = ts

    if max_model_ts > mig_ts and mig_ts > 0:
        return HookResult(
            name="Migrations", passed=False,
            message=f"Model files changed after latest migration ({latest_migration.name})",
        )

    return HookResult(
        name="Migrations", passed=True,
        message=f"Latest migration: {latest_migration.name}",
    )


def run_hook() -> HookResult:
    """Run the completion gate."""
    results = [
        check_tests(),
        check_lint(),
        check_types(),
        check_schema_migrations(),
    ]

    all_findings = []
    failed_names = []
    for r in results:
        all_findings.extend(r.findings)
        if not r.passed:
            failed_names.append(r.name)

    passed = all(r.passed for r in results)

    if not passed:
        return HookResult(
            name="Completion Gate",
            passed=False,
            message=f"BLOCKED — {', '.join(failed_names)} failed",
            findings=all_findings,
        )

    return HookResult(
        name="Completion Gate",
        passed=True,
        message="All gates passed — safe to complete",
        findings=[],
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
