#!/usr/bin/env python3
"""Master hook runner.

Usage:
    python .claude/hooks/run_hooks.py              # Run all hooks
    python .claude/hooks/run_hooks.py ui-review    # Run specific hook
    python .claude/hooks/run_hooks.py --phase pre  # Run hooks by phase

Phases:
    pre-commit:  ui-review, code-quality, contract
    pre-push:    code-quality, architecture, contract, docs-consistency
    pre-merge:   all hooks
    on-change:   ui-review (if frontend), code-quality, contract
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = ROOT / ".claude" / "hooks"

HOOKS = {
    "ui-review": "ui-review/hook.py",
    "code-quality": "code-quality/hook.py",
    "contract": "contract/hook.py",
    "architecture": "architecture/hook.py",
    "docs-consistency": "docs-consistency/hook.py",
    "planning": "planning/hook.py",
    "playwright": "playwright/hook.py",
    "completion-gate": "completion-gate/hook.py",
    "repo-health": "repo-health/hook.py",
    "decision-tracking": "decision-tracking/hook.py",
    "skill-discovery": "skill-discovery/hook.py",
}

PHASES = {
    "pre-commit": ["ui-review", "code-quality"],
    "pre-push": ["code-quality", "architecture", "contract", "docs-consistency", "skill-discovery"],
    "pre-merge": list(HOOKS.keys()),
    "on-change": ["code-quality", "contract"],
}


def load_hook(name, script_path):
    """Dynamically load and run a hook module."""
    spec = importlib.util.spec_from_file_location(f"hook_{name}", script_path)
    if not spec or not spec.loader:
        print(f"  ✗ Could not load {name}")
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "run_hook"):
        return module.run_hook()
    print(f"  ✗ {name}: no run_hook() function")
    return None


def main():
    args = sys.argv[1:]

    if not args:
        # Run all hooks
        hook_names = list(HOOKS.keys())
    elif args[0] == "--phase":
        phase = args[1] if len(args) > 1 else "pre-push"
        hook_names = PHASES.get(phase, [])
        if not hook_names:
            print(f"Unknown phase: {phase}")
            print(f"Valid phases: {', '.join(PHASES.keys())}")
            return 1
    else:
        hook_names = [a for a in args if a in HOOKS]
        if not hook_names:
            print(f"Unknown hook(s): {', '.join(args)}")
            print(f"Valid hooks: {', '.join(HOOKS.keys())}")
            return 1

    print("=" * 60)
    print("  CORTEX HOOK SYSTEM")
    print("=" * 60)

    results = []
    for name in hook_names:
        script = HOOKS_DIR / HOOKS[name]
        if not script.exists():
            print(f"  ✗ {name}: script not found")
            continue

        print(f"\n--- {name} ---")
        result = load_hook(name, script)
        if result:
            results.append(result)
            icon = "✓" if result.passed else "✗"
            print(f"  {icon} {result.name}: {result.message}")
            for f in result.findings[:5]:
                print(f"    {f}")

    # Summary
    print(f"\n{'=' * 60}")
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    failed = total - passed

    if failed > 0:
        print(f"  ✗ {failed}/{total} hooks failed")
        for r in results:
            if not r.passed:
                print(f"    ✗ {r.name}: {r.message}")
        print("=" * 60)
        return 1
    else:
        print(f"  ✓ All {total} hooks passed")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
