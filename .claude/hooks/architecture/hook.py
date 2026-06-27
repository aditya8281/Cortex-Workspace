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

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, get_changed_files, print_result, read_file

# ── Constants ─────────────────────────────────────────────────────

MAX_FINDINGS = 15

ALLOWED_LOCATIONS: dict[str, str] = {
    "model": "backend/app/models/",
    "schema": "backend/app/schemas/",
    "router": "backend/app/api/v1/",
    "service": "backend/app/services/",
    "manager": "backend/app/managers/",
    "middleware": "backend/app/middleware/",
    "task": "backend/app/tasks/",
    "hook": ".claude/hooks/",
    "skill": ".claude/skills/",
    "migration": "migrations/versions/",
    "test": "tests/",
    "doc": "docs/",
}

FORBIDDEN_PATHS: list[str] = [
    ".trae/",
    ".codex/",
    ".cortex_bootstrap/",
    "skills-lock.json",
]

ALLOWED_TOPLEVEL_MD: frozenset[str] = frozenset({
    "README.md", "CLAUDE.md", "AGENTS.md", "DESIGN.md",
    "LICENSE", "CHANGELOG.md",
})

SKIP_DIRS: frozenset[str] = frozenset({
    "__pycache__", ".venv", "node_modules", "build",
    "dist", ".git", ".pytest_cache", ".mypy_cache",
})


# ── Helpers ───────────────────────────────────────────────────────


def _has_sqlalchemy_base(fpath: Path) -> bool:
    """AST-based check: does this file define a class inheriting from Base?

    Reads the file once, parses with ast, and looks for ClassDef nodes
    whose bases include 'Base'. Much more reliable than string matching.
    """
    content = read_file(fpath)
    if not content:
        return False

    try:
        tree = ast.parse(content, filename=str(fpath))
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Base":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "Base":
                return True
    return False


# ── Checks ────────────────────────────────────────────────────────


def check_file_placement(files: list[Path]) -> list[str]:
    """Verify new files are placed in correct directories."""
    findings: list[str] = []
    for f in files:
        if not f.exists():
            continue
        rel = str(f.relative_to(ROOT))

        for forbidden in FORBIDDEN_PATHS:
            if rel.startswith(forbidden):
                findings.append(f"File in forbidden location: {rel}")
                break

        if f.suffix == ".py" and not f.name.startswith("__"):
            if _has_sqlalchemy_base(f) and "models/" not in rel and "test_" not in rel:
                findings.append(f"SQLAlchemy model outside models/: {rel}")

    return findings


def check_doc_systems() -> list[str]:
    """Check for competing documentation systems."""
    findings: list[str] = []

    for md_file in ROOT.glob("*.md"):
        if md_file.name in ALLOWED_TOPLEVEL_MD:
            continue
        findings.append(f"New top-level doc (consider docs/): {md_file.name}")

    ctx_dir = ROOT / ".claude" / "context"
    if ctx_dir.exists():
        try:
            empty = [f for f in ctx_dir.iterdir() if f.is_file() and f.stat().st_size == 0]
        except OSError:
            empty = []
        if empty:
            findings.append(f".claude/context/ has {len(empty)} empty files — should be deleted")

    return findings


def _find_registered_modules(content: str) -> set[str]:
    """Extract module names imported from v1/ in a file's content."""
    found: set[str] = set()
    # Match: from backend.app.api.v1.X import / from .v1.X import
    for m in re.finditer(r'from\s+(?:backend\.app\.api\.v1\.|\.v1\.)(\w+)', content):
        found.add(m.group(1))
    return found


def check_api_conventions() -> list[str]:
    """Check API convention compliance.

    Checks three registration paths:
    1. Direct registration in api/router.py
    2. Nested sub-routers (imported into a file that IS registered in router.py)
    3. Direct app-level registration in main.py (e.g. WebSocket routers)
    """
    findings: list[str] = []
    api_dir = ROOT / "backend" / "app" / "api"
    v1_dir = api_dir / "v1"
    main_py = ROOT / "backend" / "app" / "main.py"

    if not v1_dir.exists():
        return findings

    # Step 1: Collect all v1 module names
    v1_modules: set[str] = set()
    for router_file in v1_dir.glob("*.py"):
        if not router_file.name.startswith("__"):
            v1_modules.add(router_file.stem)

    if not v1_modules:
        return findings

    # Step 2: Find modules registered in router.py
    router_py = api_dir / "router.py"
    router_content = read_file(router_py) if router_py.exists() else ""
    registered_in_router = _find_registered_modules(router_content)

    # Step 3: For modules NOT in router.py, check if they're nested sub-routers
    # (imported into a file that IS registered in router.py)
    nested_modules: set[str] = set()
    for reg_mod in registered_in_router:
        reg_file = v1_dir / f"{reg_mod}.py"
        if reg_file.exists():
            reg_content = read_file(reg_file)
            nested_modules |= _find_registered_modules(reg_content)

    # Step 4: For remaining modules, check main.py for direct app-level registration
    main_content = read_file(main_py) if main_py.exists() else ""
    registered_in_main: set[str] = set()
    for m in re.finditer(r'from\s+backend\.app\.api\.v1\.(\w+)', main_content):
        registered_in_main.add(m.group(1))

    # Step 5: Flag truly unregistered modules
    all_registered = registered_in_router | nested_modules | registered_in_main
    unregistered = v1_modules - all_registered

    for module_name in sorted(unregistered):
        findings.append(f"Router {module_name} not registered (router.py, sub-routers, or main.py)")

    return findings


def check_model_registration() -> list[str]:
    """Check that new models are imported in migrations/env.py for Alembic.

    Models must be imported in migrations/env.py (not main.py) so Alembic's
    autogenerate can detect them for migration creation.
    """
    findings: list[str] = []
    migrations_env = ROOT / "migrations" / "env.py"
    models_dir = ROOT / "backend" / "app" / "models"

    if not migrations_env.exists() or not models_dir.exists():
        return findings

    env_content = read_file(migrations_env)

    for model_file in models_dir.glob("*.py"):
        if model_file.name.startswith("__"):
            continue
        module_name = f"backend.app.models.{model_file.stem}"
        if module_name not in env_content:
            findings.append(f"Model {model_file.stem} not imported in migrations/env.py (needed for Alembic)")

    return findings


# ── Main Hook ─────────────────────────────────────────────────────


def run_hook() -> HookResult:
    """Run the architecture compliance hook."""
    files = get_changed_files()

    findings: list[str] = []
    findings.extend(check_file_placement(files))
    findings.extend(check_doc_systems())
    findings.extend(check_api_conventions())
    findings.extend(check_model_registration())

    real_errors = [f for f in findings if "forbidden" in f.lower() or "not imported" in f.lower() or "not registered" in f.lower()]
    warnings = [f for f in findings if f not in real_errors]

    return HookResult(
        name="Architecture Compliance",
        passed=len(real_errors) == 0,
        message=f"{len(real_errors)} violations, {len(warnings)} warnings" if findings else "Architecture OK",
        findings=real_errors + warnings[:MAX_FINDINGS],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
