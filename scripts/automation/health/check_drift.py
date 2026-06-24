#!/usr/bin/env python3
"""Repository health: Architecture and documentation drift detection.

Checks:
- Architecture drift: code structure vs documented structure
- Documentation drift: stale or missing doc updates
- Pattern drift: inconsistent naming, imports, error handling
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def check_architecture_drift():
    """Check if actual code structure matches documented architecture."""
    findings = []

    arch_doc = ROOT / "docs" / "ARCHITECTURE.md"
    if not arch_doc.exists():
        return ["docs/ARCHITECTURE.md not found"]

    # Check documented directories exist
    arch_content = arch_doc.read_text()
    dir_pattern = re.compile(r'`?(backend/app/\w+/)`?')
    documented_dirs = set(dir_pattern.findall(arch_content))

    actual_dirs = set()
    backend_app = ROOT / "backend" / "app"
    if backend_app.exists():
        actual_dirs = {
            f"backend/app/{d.name}"
            for d in backend_app.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        }

    # Check for undocumented directories
    undocumented = actual_dirs - documented_dirs
    if undocumented:
        for d in sorted(undocumented):
            findings.append(f"  Undocumented directory: {d}")

    # Check for documented but non-existent directories
    ghost_dirs = documented_dirs - actual_dirs
    if ghost_dirs:
        for d in sorted(ghost_dirs):
            findings.append(f"  Ghost directory (documented but missing): {d}")

    return findings


def check_doc_drift():
    """Check for stale documentation."""
    findings = []

    # Check if README mentions files that don't exist
    readme = ROOT / "README.md"
    if readme.exists():
        content = readme.read_text()
        # Check referenced files
        file_refs = re.findall(r'\[.*?\]\(([^)]+\.md)\)', content)
        for ref in file_refs:
            # Convert relative links to actual paths
            if ref.startswith("docs/"):
                p = ROOT / ref
                if not p.exists():
                    findings.append(f"  README.md links to non-existent: {ref}")

    # Check if docs reference each other
    docs_dir = ROOT / "docs"
    if docs_dir.exists():
        for doc in docs_dir.glob("*.md"):
            content = doc.read_text()
            internal_refs = re.findall(r'\[.*?\]\(([^)]+\.md)\)', content)
            for ref in internal_refs:
                if ref.startswith("/"):
                    continue  # Absolute paths
                target = doc.parent / ref
                if not target.exists():
                    findings.append(f"  {doc.name} links to non-existent: {ref}")

    return findings


def check_pattern_drift():
    """Check for inconsistent patterns across codebase."""
    findings = []

    # Check auth patterns — all user-scoped endpoints should use get_current_user
    api_dir = ROOT / "backend" / "app" / "api" / "v1"
    if api_dir.exists():
        for router_file in api_dir.glob("*.py"):
            content = router_file.read_text()
            # Simple check: if file has user_id in queries but no get_current_user import
            if "user_id" in content and "get_current_user" not in content:
                findings.append(f"  {router_file.name}: references user_id but doesn't import get_current_user")

    return findings


def check_drift():
    errors = []
    warnings = []

    # Architecture drift
    arch_findings = check_architecture_drift()
    if arch_findings:
        warnings.extend(arch_findings)
        print(f"Architecture drift: {len(arch_findings)} findings")
    else:
        print("Architecture drift: none ✓")

    # Doc drift
    doc_findings = check_doc_drift()
    if doc_findings:
        warnings.extend(doc_findings)
        print(f"Documentation drift: {len(doc_findings)} findings")
    else:
        print("Documentation drift: none ✓")

    # Pattern drift
    pattern_findings = check_pattern_drift()
    if pattern_findings:
        warnings.extend(pattern_findings)
        print(f"Pattern drift: {len(pattern_findings)} findings")
    else:
        print("Pattern drift: none ✓")

    if warnings:
        print("\nDrift findings:")
        for w in warnings:
            print(w)

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(e)
        return 1

    print("\n✓ Drift check complete")
    return 0


if __name__ == "__main__":
    sys.exit(check_drift())
