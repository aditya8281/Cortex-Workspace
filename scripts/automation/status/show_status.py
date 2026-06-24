#!/usr/bin/env python3
"""Show current CORTEX development status.

Reads ACTIVE_VERSION.md and progress files to report what version/phase is active.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main():
    print("=" * 50)
    print("  CORTEX STATUS")
    print("=" * 50)

    # Read ACTIVE_VERSION.md
    active_file = ROOT / ".agents" / "plans" / "ACTIVE_VERSION.md"
    if active_file.exists():
        content = active_file.read_text()
        # Extract version
        version_match = re.search(r'\*\*Current Version:\*\*\s*(.+)', content)
        phase_match = re.search(r'\*\*Current Phase:\*\*\s*(.+)', content)
        if version_match:
            print(f"  Version: {version_match.group(1).strip()}")
        if phase_match:
            print(f"  Phase: {phase_match.group(1).strip()}")
    else:
        print("  ⚠ ACTIVE_VERSION.md not found")
        print("  Default: V1 — The Brain Works")

    # Count progress across all versions
    progress_dir = ROOT / ".agents" / "plans" / "versions"
    if progress_dir.exists():
        total = 0
        completed = 0
        for v_dir in sorted(progress_dir.iterdir()):
            if not v_dir.is_dir():
                continue
            progress_file = v_dir / "progress.md"
            if progress_file.exists():
                content = progress_file.read_text()
                total += content.count("⬜")
                completed += content.count("✅") + content.count("☑️")
        print(f"  Components: {completed} completed / {total} total")
    else:
        print("  ⚠ versions/ directory not found")

    # Recent git activity
    import subprocess
    result = subprocess.run(
        ["git", "log", "--oneline", "-5"],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    if result.stdout.strip():
        print("\n  Recent commits:")
        for line in result.stdout.strip().splitlines()[:5]:
            print(f"    {line}")

    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
