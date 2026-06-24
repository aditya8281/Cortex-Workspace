#!/usr/bin/env python3
"""Report: Development progress summary.

Scans git log, roadmap checkboxes, and test counts to produce a progress snapshot.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def git_recent_commits(n=20):
    """Get recent git commits."""
    result = subprocess.run(
        ["git", "log", f"--oneline", f"-{n}"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if result.returncode != 0:
        return []
    return result.stdout.strip().splitlines()


def roadmap_progress():
    """Count completed vs total roadmap items."""
    roadmap = ROOT / "docs" / "ROADMAP.md"
    if not roadmap.exists():
        return None, None

    content = roadmap.read_text()
    done = len(re.findall(r'\[x\]', content, re.IGNORECASE))
    total = done + len(re.findall(r'\[ \]', content))
    return done, total


def test_count():
    """Count test functions in the test suite."""
    test_dir = ROOT / "tests"
    if not test_dir.exists():
        return 0
    count = 0
    for f in test_dir.glob("**/test_*.py"):
        try:
            content = f.read_text()
            count += len(re.findall(r'^def test_\w+', content, re.MULTILINE))
        except (UnicodeDecodeError, PermissionError):
            continue
    return count


def generate_report():
    print("=" * 60)
    print("  CORTEX DEVELOPMENT PROGRESS REPORT")
    print("=" * 60)
    print()

    # Git
    commits = git_recent_commits(20)
    print(f"  Recent commits: {len(commits)}")
    for c in commits[:5]:
        print(f"    {c}")
    if len(commits) > 5:
        print(f"    ... and {len(commits) - 5} more")
    print()

    # Roadmap
    done, total = roadmap_progress()
    if total:
        pct = int(done / total * 100) if total > 0 else 0
        print(f"  Roadmap: {done}/{total} items complete ({pct}%)")
        bar_len = 30
        filled = int(bar_len * done / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"  [{bar}] {pct}%")
    print()

    # Tests
    test_cnt = test_count()
    print(f"  Test functions: {test_cnt}")
    print()

    # Phases
    roadmap = ROOT / "docs" / "ROADMAP.md"
    if roadmap.exists():
        content = roadmap.read_text()
        phases = re.findall(r'### Phase (\d+[A-B]?):\s+(.+?)\s*([✅🟡⬜])', content)
        if phases:
            print("  Phase Status:")
            for num, name, status in phases:
                print(f"    Phase {num}: {name} {status}")
    print()

    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(generate_report())
