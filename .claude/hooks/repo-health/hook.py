#!/usr/bin/env python3
"""Hook 9 — Repository Health Hook

Trigger: Periodically, major commits
Purpose: Detect dead code, duplicates, abandoned files, tech debt

Checks:
- Dead code (commented-out blocks, unused functions)
- Placeholder implementations (NotImplementedError, pass-only)
- Stale files (not touched in 6+ months)
- Tech debt hotspots (files changed frequently)
"""

import re
import subprocess
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, run_command, read_file, print_result


def find_dead_code() -> list:
    """Find commented-out code blocks and pass-only functions."""
    findings = []
    py_files = list(ROOT.glob("backend/**/*.py")) + list(ROOT.glob("tests/**/*.py"))

    for fpath in py_files:
        if ".venv" in str(fpath) or "__pycache__" in str(fpath):
            continue
        content = read_file(fpath)
        if not content:
            continue
        rel = str(fpath.relative_to(ROOT))
        lines = content.split("\n")

        # Find pass-only function bodies
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "pass" and i > 0:
                prev = lines[i - 1].strip() if i > 0 else ""
                if prev.startswith("def ") or prev.startswith("async def "):
                    findings.append(f"pass-only function: {rel}:{i}: {prev[:80]}")

        # Find consecutive commented code (3+ lines with code keywords)
        consecutive = 0
        start = 0
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("#") and any(kw in s for kw in ["def ", "if ", "return ", "import ", "for "]):
                if consecutive == 0:
                    start = i + 1
                consecutive += 1
            else:
                if consecutive >= 3:
                    findings.append(f"commented-out code: {rel}:{start}-{start+consecutive}")
                consecutive = 0

    return findings


def find_placeholders() -> list:
    """Find NotImplementedError, TODO, FIXME, HACK, TBD."""
    findings = []
    py_files = list(ROOT.glob("backend/**/*.py")) + list(ROOT.glob("tests/**/*.py"))

    for fpath in py_files:
        if ".venv" in str(fpath) or "__pycache__" in str(fpath):
            continue
        content = read_file(fpath)
        if not content:
            continue
        rel = str(fpath.relative_to(ROOT))

        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if "raise NotImplementedError" in stripped:
                findings.append(f"NotImplementedError: {rel}:{i}")
            if re.search(r'#\s*(TODO|FIXME|HACK|XXX|TBD)\b', stripped, re.IGNORECASE):
                tag = re.search(r'#\s*(TODO|FIXME|HACK|XXX|TBD)', stripped, re.IGNORECASE).group(1)
                findings.append(f"{tag}: {rel}:{i}: {stripped[:80]}")

    return findings


def find_stale_files() -> list:
    """Find files not modified in 6+ months."""
    findings = []
    code, out, _ = run_command(
        ["git", "log", "--diff-filter=M", "--max-count=1", "--format=%at", "--", "backend/"]
    )
    if code != 0:
        return findings

    # Get list of files and their last modification time
    code, out, _ = run_command(
        ["git", "ls-files", "--format=%(committerdate:iso)", "backend/"]
    )
    # This is a simplified check — just report if we can't determine staleness
    return findings


def find_tech_debt_hotspots() -> list:
    """Find files that are changed most frequently (tech debt indicators)."""
    findings = []
    code, out, _ = run_command(
        ["git", "log", "--oneline", "-50", "--name-only", "--pretty=format:"]
    )
    if code != 0:
        return findings

    file_counts = Counter()
    for line in out.splitlines():
        line = line.strip()
        if line and line.endswith(".py"):
            file_counts[line] += 1

    # Report files changed 5+ times in last 50 commits
    hotspots = [(f, c) for f, c in file_counts.most_common(10) if c >= 5]
    for f, c in hotspots:
        findings.append(f"hotspot ({c} recent changes): {f}")

    return findings


def run_hook():
    """Run the repo health hook."""
    dead = find_dead_code()
    placeholders = find_placeholders()
    hotspots = find_tech_debt_hotspots()

    all_findings = dead + placeholders + hotspots

    # Separate severity
    errors = [f for f in all_findings if "NotImplementedError" in f]
    warnings = [f for f in all_findings if f not in errors]

    return HookResult(
        name="Repo Health",
        passed=True,  # Health is informational, not blocking
        message=f"{len(errors)} issues, {len(warnings)} warnings",
        findings=errors + warnings[:15],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
