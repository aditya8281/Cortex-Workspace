#!/usr/bin/env python3
"""Release workflow: comprehensive pre-release validation.

Checks:
1. All tests pass
2. Lint clean
3. Build succeeds
4. Documentation updated
5. No P0/P1 placeholders
6. No security issues
7. Governance hooks pass
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def run(cmd, timeout=120):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def check(name, cmd):
    code, out, err = run(cmd)
    icon = "✓" if code == 0 else "✗"
    print(f"  {icon} {name}")
    if code != 0:
        summary = (out + err).strip().splitlines()[-3:]
        for line in summary:
            print(f"    {line}")
    return code == 0


def main():
    print("=" * 50)
    print("  RELEASE VALIDATION")
    print("=" * 50)

    results = []
    results.append(check("Tests", ["uv", "run", "pytest", "-v", "--tb=short"]))
    results.append(check("Lint", ["uv", "run", "ruff", "check", "backend/", "tests/"]))
    results.append(check("Format check", ["uv", "run", "ruff", "format", "--check", "backend/", "tests/"]))
    results.append(check("Types", ["uv", "run", "mypy", "backend/", "--ignore-missing-imports",
                                   "--explicit-package-bases", "--implicit-optional"]))
    results.append(check("Frontend lint", ["bash", "-c", "cd frontend && npx next lint"]))
    results.append(check("Frontend types", ["bash", "-c", "cd frontend && npx tsc --noEmit"]))
    results.append(check("Frontend tests", ["bash", "-c", "cd frontend && npx vitest run"]))
    results.append(check("Frontend build", ["bash", "-c", "cd frontend && npm run build"]))
    results.append(check("No placeholders", [sys.executable, str(ROOT / "scripts/automation/bug_discovery/find_placeholders.py")]))
    results.append(check("Security", [sys.executable, str(ROOT / "scripts/automation/bug_discovery/check_security.py")]))
    results.append(check("Docs check", [sys.executable, str(ROOT / "scripts/automation/completion/check_docs.py")]))
    results.append(check("Governance hooks", [sys.executable, str(ROOT / ".claude/hooks/run_hooks.py"), "--phase", "pre-push"]))

    print(f"\n{'=' * 50}")
    passed = sum(results)
    total = len(results)
    if all(results):
        print(f"  ✓ All {total} release checks passed")
    else:
        print(f"  ✗ {total - passed}/{total} release checks failed")
    print("=" * 50)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
