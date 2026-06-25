#!/usr/bin/env python3
"""Repository health: Detect duplicate/similar code.

Checks:
- Duplicate skill directories (should only be .claude/skills/)
- Duplicate configuration files
- Similar Python function names across modules
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def find_duplicate_skills():
    """Check for duplicate skill directories."""
    known_locations = [
        (".claude/skills", "Primary skill directory"),
        (".trae/skills", "Trae skills (should not exist — duplicates .claude/skills/)"),
    ]

    found = {}
    for path_str, desc in known_locations:
        p = ROOT / path_str
        if p.exists():
            skills = [d.name for d in p.iterdir() if d.is_dir()]
            found[path_str] = {"desc": desc, "count": len(skills), "skills": skills}

    if len(found) > 1:
        print("DUPLICATE SKILL DIRECTORIES DETECTED:")
        for path_str, info in found.items():
            print(f"  {path_str}: {info['count']} skills — {info['desc']}")
        return True

    if found:
        path_str, info = next(iter(found.items()))
        print(f"Skills: {info['count']} in {path_str} ✓")

    return False


def find_duplicate_configs():
    """Check for duplicate configuration files."""
    config_patterns = [
        (".github/hooks/impeccable.json", ".claude/settings.local.json"),
    ]

    for left, right in config_patterns:
        left_p = ROOT / left
        right_p = ROOT / right
        if left_p.exists() and right_p.exists():
            print(f"Duplicate config: {left} and {right}")
            return True

    print("Config files: no duplicates ✓")
    return False


def find_duplicate_functions():
    """Find Python functions with identical names across different modules."""
    func_names = {}
    py_files = list(ROOT.glob("backend/app/**/*.py"))

    for fpath in py_files:
        if "__pycache__" in str(fpath):
            continue
        try:
            content = fpath.read_text()
            # Simple regex for function definitions
            import re
            for match in re.finditer(r'def (\w+)\s*\(', content):
                name = match.group(1)
                if name.startswith("_") or name in ("get_db", "get_current_user"):
                    continue
                func_names.setdefault(name, []).append(
                    str(fpath.relative_to(ROOT))
                )
        except (UnicodeDecodeError, PermissionError):
            continue

    dupes = {name: files for name, files in func_names.items() if len(files) > 1}
    if dupes:
        print(f"Duplicate function names: {len(dupes)}")
        for name, files in sorted(dupes.items())[:5]:
            print(f"  {name}: {', '.join(files)}")
        return True

    print("Functions: no name duplicates ✓")
    return False


def check_duplicates():
    has_issues = False
    has_issues |= find_duplicate_skills()
    has_issues |= find_duplicate_configs()
    has_issues |= find_duplicate_functions()

    if has_issues:
        print("\n⚠ Duplicate code found")
        return 1

    print("\n✓ Duplicate code check passed")
    return 0


if __name__ == "__main__":
    sys.exit(check_duplicates())
