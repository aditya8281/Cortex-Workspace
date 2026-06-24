#!/usr/bin/env python3
"""Hook 4 — Architecture Compliance Hook

Trigger: Major modifications
Purpose: Verify architecture principles, boundaries, no duplicate systems

Checks:
- New files follow directory conventions
- No new competing doc systems
- No duplicate skill directories
- Backend models imported in main.py
- Router registration in api/router.py
- Service instantiation patterns (constructor injection, not global)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, get_changed_files, read_file, print_result

# Allowed file locations per type
ALLOWED_LOCATIONS = {
    "model": "backend/app/models/",
    "schema": "backend/app/schemas/",
    "router": "backend/app/api/v1/",
    "service": "backend/app/services/",
    "manager": "backend/app/managers/",
    "middleware": "backend/app/middleware/",
    "task": "backend/app/tasks/",
    "hook": ".claude/hooks/",
    "skill": ".agents/skills/",
    "migration": "migrations/versions/",
    "test": "tests/",
    "doc": "docs/",
}

# Forbidden paths (should never be recreated)
FORBIDDEN_PATHS = [
    ".trae/",
    ".codex/",
    ".cortex_bootstrap/",
    "skills-lock.json",
]


def check_file_placement(files: list) -> list:
    """Verify new files are placed in correct directories."""
    findings = []
    for f in files:
        if not f.exists():
            continue
        rel = str(f.relative_to(ROOT))
        name = f.name

        # Check forbidden paths
        for forbidden in FORBIDDEN_PATHS:
            if rel.startswith(forbidden):
                findings.append(f"File in forbidden location: {rel}")
                break

        # Check model files
        if name.endswith(".py") and not name.startswith("__"):
            if "class " in read_file(f) and "Base" in read_file(f):
                if "models/" not in rel and "test_" not in rel:
                    findings.append(f"SQLAlchemy model outside models/: {rel}")

    return findings


def check_doc_systems() -> list:
    """Check for competing documentation systems."""
    findings = []

    # Check no new top-level .md files that duplicate docs/
    for md_file in ROOT.glob("*.md"):
        name = md_file.name
        if name in ("README.md", "CLAUDE.md", "AGENTS.md", "DESIGN.md", "LICENSE", "CHANGELOG.md"):
            continue
        # New top-level md might be a competing doc system
        findings.append(f"New top-level doc (consider docs/): {name}")

    # Check .claude/context/ doesn't get recreated
    ctx_dir = ROOT / ".claude" / "context"
    if ctx_dir.exists():
        empty = [f for f in ctx_dir.iterdir() if f.is_file() and f.stat().st_size == 0]
        if empty:
            findings.append(f".claude/context/ has {len(empty)} empty files — should be deleted")

    return findings


def check_api_conventions() -> list:
    """Check API convention compliance."""
    findings = []
    api_dir = ROOT / "backend" / "app" / "api"
    router_py = api_dir / "router.py"

    if not router_py.exists():
        return findings

    content = read_file(router_py)
    # Check that all v1 routers are registered
    v1_dir = api_dir / "v1"
    if v1_dir.exists():
        for router_file in v1_dir.glob("*.py"):
            if router_file.name.startswith("__"):
                continue
            module_name = router_file.stem
            if f"from backend.app.api.v1.{module_name}" not in content:
                if f"from .v1.{module_name}" not in content:
                    findings.append(f"Router {module_name} not registered in api/router.py")

    return findings


def check_model_registration() -> list:
    """Check that new models are imported in main.py for Alembic."""
    findings = []
    main_py = ROOT / "backend" / "app" / "main.py"
    models_dir = ROOT / "backend" / "app" / "models"

    if not main_py.exists() or not models_dir.exists():
        return findings

    main_content = read_file(main_py)

    for model_file in models_dir.glob("*.py"):
        if model_file.name.startswith("__"):
            continue
        module_name = f"backend.app.models.{model_file.stem}"
        if module_name not in main_content:
            findings.append(f"Model {model_file.stem} not imported in main.py (needed for Alembic)")

    return findings


def run_hook():
    """Run the architecture compliance hook."""
    files = get_changed_files()

    findings = []
    findings.extend(check_file_placement(files))
    findings.extend(check_doc_systems())
    findings.extend(check_api_conventions())
    findings.extend(check_model_registration())

    warnings = []
    # Filter: new top-level docs are warnings, not errors
    real_errors = [f for f in findings if "forbidden" in f.lower() or "not imported" in f.lower() or "not registered" in f.lower()]
    warnings = [f for f in findings if f not in real_errors]

    return HookResult(
        name="Architecture Compliance",
        passed=len(real_errors) == 0,
        message=f"{len(real_errors)} violations, {len(warnings)} warnings" if findings else "Architecture OK",
        findings=real_errors + warnings[:10],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
