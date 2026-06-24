#!/usr/bin/env python3
"""Repository health: Check for unused dependencies.

Compares pyproject.toml imports against actual usage in codebase.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def get_declared_deps():
    """Extract dependencies from pyproject.toml."""
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        return set()

    content = pyproject.read_text()
    deps = set()

    # Match dependencies in [project] dependencies
    in_deps = False
    for line in content.splitlines():
        if "dependencies" in line and "[" in line:
            in_deps = True
            continue
        if in_deps:
            if line.strip().startswith("]"):
                in_deps = False
                continue
            match = re.match(r'\s*["\']([^"\'">=<\[]+)', line)
            if match:
                dep = match.group(1).strip()
                # Normalize: take only package name before any extras
                dep = dep.split("[")[0]
                deps.add(dep.lower().replace("-", "_"))

    return deps


def get_used_deps():
    """Find actual imports in Python code."""
    used = set()
    py_files = list(ROOT.glob("backend/**/*.py")) + list(ROOT.glob("tests/**/*.py"))

    for fpath in py_files:
        if ".venv" in str(fpath) or "__pycache__" in str(fpath):
            continue
        try:
            content = fpath.read_text()
        except (UnicodeDecodeError, PermissionError):
            continue

        for match in re.finditer(r'^(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE):
            used.add(match.group(1).lower())

    return used


def check_dependencies():
    declared = get_declared_deps()
    used = get_used_deps()

    if not declared:
        print("Could not parse pyproject.toml dependencies")
        return 0

    # Standard library and known false negatives
    stdlib = {
        "os", "sys", "re", "json", "pathlib", "typing", "datetime",
        "collections", "functools", "itertools", "hashlib", "uuid",
        "io", "ast", "subprocess", "logging", "time", "math", "base64",
        "hmac", "struct", "secrets", "textwrap", "abc", "copy", "enum",
        "dataclasses", "contextlib", "glob", "shutil", "tempfile",
    }

    unused = declared - used - stdlib - {"backend", "app"}
    missing_imports = used - declared - stdlib

    print(f"Declared: {len(declared)} packages")
    print(f"Used in code: {len(used)} top-level imports")

    if unused:
        print(f"\nPossibly unused dependencies ({len(unused)}):")
        for dep in sorted(unused):
            print(f"  {dep}")

    if missing_imports and len(missing_imports) < 20:
        print(f"\nImports not in pyproject.toml ({len(missing_imports)}):")
        for imp in sorted(missing_imports)[:10]:
            print(f"  {imp}")

    print("\n✓ Dependency check complete (review manually)")
    return 0


if __name__ == "__main__":
    sys.exit(check_dependencies())
