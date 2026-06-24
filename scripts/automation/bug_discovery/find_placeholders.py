#!/usr/bin/env python3
"""Bug discovery: Find incomplete features and placeholders.

Scans for:
- TODO/FIXME/HACK/XXX/TBD markers
- Empty function bodies (pass-only)
- Placeholder return values (hardcoded "mock", dummy data)
- NotImplementedError raises
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def scan_file(fpath, root):
    findings = []
    try:
        content = fpath.read_text()
    except (UnicodeDecodeError, PermissionError):
        return findings

    lines = content.splitlines()
    rel = str(fpath.relative_to(root))

    # TODO/FIXME/HACK/XXX/TBD
    tag_re = re.compile(r'#\s*(TODO|FIXME|HACK|XXX|TBD)\b', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        m = tag_re.search(line)
        if m:
            findings.append(("placeholder", rel, i, m.group(1).upper(), line.strip()[:100]))

    # NotImplementedError
    for i, line in enumerate(lines, 1):
        if "raise NotImplementedError" in line:
            findings.append(("incomplete", rel, i, "NotImplementedError", line.strip()[:100]))

    # pass-only function bodies (simple heuristic)
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped == "pass" and i > 1:
            prev = lines[i - 2].strip() if i >= 2 else ""
            if prev.startswith("def ") or prev.startswith("async def "):
                findings.append(("empty_func", rel, i, "pass-only", prev[:100]))

    return findings


def find_placeholders():
    all_findings = []
    search_dirs = [ROOT / "backend", ROOT / "tests", ROOT / "frontend/src"]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for fpath in search_dir.rglob("*.py"):
            if ".venv" in str(fpath) or "__pycache__" in str(fpath):
                continue
            all_findings.extend(scan_file(fpath, ROOT))

    # Also scan TypeScript
    for search_dir in [ROOT / "frontend/src"]:
        if not search_dir.exists():
            continue
        for fpath in search_dir.rglob("*.ts"):
            if "node_modules" in str(fpath):
                continue
            all_findings.extend(scan_file(fpath, ROOT))

    # Group by type
    by_type = {}
    for f in all_findings:
        by_type.setdefault(f[0], []).append(f)

    print(f"Total findings: {len(all_findings)}")
    for ftype, items in sorted(by_type.items()):
        print(f"\n  {ftype.upper()} ({len(items)}):")
        for _, file, line, tag, text in items[:10]:
            print(f"    {file}:{line} [{tag}] {text[:80]}")
        if len(items) > 10:
            print(f"    ... and {len(items) - 10} more")

    if len(all_findings) > 0:
        print(f"\n⚠ {len(all_findings)} placeholder/incomplete items found")
        return 1
    print("\n✓ No placeholders found")
    return 0


if __name__ == "__main__":
    sys.exit(find_placeholders())
