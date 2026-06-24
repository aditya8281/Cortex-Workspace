#!/usr/bin/env python3
"""Claude Code Hook: Pre-commit governance gate.

Runs code-quality + contract checks before any file write/commit.
Wired into settings.local.json PostToolUse on Edit|Write|MultiEdit.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = ROOT / ".claude" / "hooks"
RUNNER = HOOKS_DIR / "run_hooks.py"


def run_hook(hook_name: str) -> tuple[int, str]:
    """Run a single governance hook and return (exit_code, output)."""
    try:
        result = subprocess.run(
            [sys.executable, str(RUNNER), hook_name],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=30,
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, f"Hook {hook_name} timed out after 30s"
    except Exception as e:
        return 1, f"Hook {hook_name} error: {e}"


def main():
    """Run code-quality and contract checks."""
    hooks_to_run = ["code-quality", "contract"]
    failed = []
    outputs = []

    for hook in hooks_to_run:
        code, output = run_hook(hook)
        outputs.append(f"--- {hook} ---\n{output}")
        if code != 0:
            failed.append(hook)

    if failed:
        combined = "\n\n".join(outputs)
        print(f"GOVERNANCE GATE FAILED: {', '.join(failed)}")
        print(combined[:2000])  # Truncate long output
        sys.exit(1)
    else:
        print("Governance gate passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
