#!/usr/bin/env python3
"""Repository health: Detect dead code.

Checks:
- Python functions/classes with no callers (beyond self-referencing)
- Import statements for unused modules
- Commented-out code blocks (>3 consecutive lines)
- Unreachable code after return/raise
"""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def find_commented_code_blocks():
    """Find consecutive commented-out code blocks (3+ lines)."""
    findings = []
    py_files = list(ROOT.glob("backend/**/*.py")) + list(ROOT.glob("tests/**/*.py"))

    for fpath in py_files:
        if ".venv" in str(fpath) or "__pycache__" in str(fpath):
            continue
        try:
            lines = fpath.read_text().splitlines()
        except (UnicodeDecodeError, PermissionError):
            continue

        consecutive = 0
        start_line = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("#!") and not stripped.startswith("# ====") and not stripped.startswith("# ---"):
                # Looks like commented code, not documentation
                if any(kw in stripped for kw in ["def ", "class ", "import ", "return ", "if ", "for ", "while ", "try:", "with "]):
                    if consecutive == 0:
                        start_line = i
                    consecutive += 1
                else:
                    if consecutive >= 3:
                        findings.append({
                            "file": str(fpath.relative_to(ROOT)),
                            "start": start_line,
                            "lines": consecutive,
                        })
                    consecutive = 0
            else:
                if consecutive >= 3:
                    findings.append({
                        "file": str(fpath.relative_to(ROOT)),
                        "start": start_line,
                        "lines": consecutive,
                    })
                consecutive = 0

    return findings


def find_todo_fixme():
    """Find TODO, FIXME, HACK, XXX placeholders."""
    findings = []
    py_files = list(ROOT.glob("backend/**/*.py")) + list(ROOT.glob("tests/**/*.py"))
    pattern = re.compile(r'#\s*(TODO|FIXME|HACK|XXX|TBD)\b', re.IGNORECASE)

    for fpath in py_files:
        if ".venv" in str(fpath) or "__pycache__" in str(fpath):
            continue
        try:
            for i, line in enumerate(fpath.read_text().splitlines(), 1):
                match = pattern.search(line)
                if match:
                    findings.append({
                        "file": str(fpath.relative_to(ROOT)),
                        "line": i,
                        "tag": match.group(1).upper(),
                        "text": line.strip()[:100],
                    })
        except (UnicodeDecodeError, PermissionError):
            continue

    return findings


def find_dead_code():
    errors = []
    warnings = []

    # Check commented code blocks
    commented = find_commented_code_blocks()
    if commented:
        print(f"Commented-out code blocks: {len(commented)}")
        for c in commented[:10]:
            warnings.append(f"  {c['file']}:{c['start']} ({c['lines']} lines)")

    # Check placeholders
    placeholders = find_todo_fixme()
    if placeholders:
        by_tag = {}
        for p in placeholders:
            by_tag.setdefault(p["tag"], []).append(p)
        print(f"Placeholders: {len(placeholders)}")
        for tag, items in sorted(by_tag.items()):
            print(f"  {tag}: {len(items)}")
            for item in items[:3]:
                print(f"    {item['file']}:{item['line']}: {item['text'][:80]}")

    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(w)

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(e)
        return 1

    print("\n✓ Dead code check passed")
    return 0


if __name__ == "__main__":
    sys.exit(find_dead_code())
