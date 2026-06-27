#!/usr/bin/env python3
"""Shared utilities for Cortex hooks.

Common functions used across all hook implementations.
"""

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class HookResult:
    """Standard result from any hook."""
    name: str
    passed: bool
    message: str
    findings: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def to_dict(self):
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "findings": self.findings,
            "warnings": self.warnings,
        }


def run_command(cmd: list, cwd: Path | None = None, timeout: int = 120) -> tuple:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd or ROOT),
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def run_make(target: str) -> tuple:
    """Run a Makefile target and return (returncode, stdout, stderr)."""
    return run_command(["make", target])


def run_python(script: str) -> tuple:
    """Run a Python script from scripts/automation/ and return (returncode, stdout, stderr)."""
    script_path = ROOT / "scripts" / "automation" / script
    if not script_path.exists():
        return 1, "", f"Script not found: {script}"
    return run_command([sys.executable, str(script_path)])


def get_changed_files() -> list:
    """Get list of files changed in the current working tree."""
    code, out, _ = run_command(["git", "diff", "--name-only", "HEAD"])
    if code != 0:
        # Fallback: get all tracked files
        code, out, _ = run_command(["git", "ls-files"])
    return [ROOT / f for f in out.strip().splitlines() if f.strip()]


def get_staged_files() -> list:
    """Get list of files staged for commit."""
    code, out, _ = run_command(["git", "diff", "--cached", "--name-only"])
    return [ROOT / f for f in out.strip().splitlines() if f.strip()]


def is_frontend_file(path: Path) -> bool:
    """Check if a file is a frontend file."""
    s = str(path)
    return any(d in s for d in ["frontend/", ".tsx", ".ts", ".jsx", ".js", ".css", ".scss"])


def is_backend_file(path: Path) -> bool:
    """Check if a file is a backend file."""
    s = str(path)
    return any(d in s for d in ["backend/", ".py"]) and "test_" not in path.name


def is_test_file(path: Path) -> bool:
    """Check if a file is a test file."""
    return path.name.startswith("test_") or "/tests/" in str(path)


def is_model_file(path: Path) -> bool:
    """Check if a file is a SQLAlchemy model."""
    return path.parent.name == "models" and path.suffix == ".py"


def is_schema_file(path: Path) -> bool:
    """Check if a file is a Pydantic schema."""
    return path.parent.name == "schemas" and path.suffix == ".py"


def is_router_file(path: Path) -> bool:
    """Check if a file is an API router."""
    return path.parent.name == "v1" and path.suffix == ".py"


def read_file(path: Path) -> str:
    """Read file content, return empty string on error."""
    try:
        return path.read_text()
    except (UnicodeDecodeError, PermissionError, FileNotFoundError):
        return ""


def print_result(result: HookResult):
    """Print a formatted hook result."""
    icon = "✓" if result.passed else "✗"
    print(f"  {icon} {result.name}: {result.message}")
    for f in result.findings:
        print(f"    - {f}")
    for w in result.warnings:
        print(f"    ⚠ {w}")
