#!/usr/bin/env python3
"""Hook 9 — Repository Health Hook

Trigger: Periodically, major commits
Purpose: Detect dead code, duplicates, abandoned files, tech debt

Checks:
- Dead code (commented-out blocks, pass-only functions via AST)
- Placeholder implementations (NotImplementedError, TODO/FIXME/etc.)
- Stale files (not touched in N days, via git log)
- Tech debt hotspots (files changed frequently)
"""

from __future__ import annotations

import ast
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, print_result, read_file, run_command

# ── Constants ──────────────────────────────────────────────────────

STALE_DAYS: int = 180
COMMENT_BLOCK_MIN: int = 3
HOTSPOT_THRESHOLD: int = 5
HOTSPOT_HISTORY: int = 50
MAX_FINDINGS: int = 50

SKIP_DIRS: frozenset[str] = frozenset({
    ".venv", "__pycache__", "node_modules", "build",
    "dist", ".git", ".pytest_cache", ".mypy_cache",
})

# ── Compiled regex (once) ─────────────────────────────────────────

_RE_COMMENTED_CODE = re.compile(
    r"#\s*(def |if |return |import |for |while |class |elif |else:|try:|except )"
)
_RE_PLACEHOLDER = re.compile(
    r"#\s*(TODO|FIXME|XXX|HACK|TBD|WIP|TEMP)\b",
    re.IGNORECASE,
)
_RE_NOT_IMPL = re.compile(r"raise\s+NotImplementedError")

# ── File Discovery ────────────────────────────────────────────────


def _discover_py_files() -> list[Path]:
    """Find all Python source files, skipping irrelevant directories."""
    files: list[Path] = []
    for pattern in ("backend/**/*.py", "tests/**/*.py"):
        for fpath in ROOT.glob(pattern):
            parts = fpath.relative_to(ROOT).parts
            if any(d in SKIP_DIRS for d in parts):
                continue
            files.append(fpath)
    return files


def _rel(path: Path) -> str:
    """Return relative path string for findings."""
    return str(path.relative_to(ROOT))


# ── Dead Code Detection (AST-based) ──────────────────────────────


def _is_pass_only_body(body: list[ast.stmt]) -> bool:
    """Check if a function body is only a docstring + pass, or just pass."""
    real_stmts = [s for s in body if not (isinstance(s, ast.Expr) and isinstance(s.value, (ast.Constant, ast.Str)))]
    return len(real_stmts) == 1 and isinstance(real_stmts[0], ast.Pass)


def _find_pass_only_functions(fpath: Path) -> list[str]:
    """Use AST to find pass-only function bodies."""
    content = read_file(fpath)
    if not content:
        return []

    rel = _rel(fpath)
    findings: list[str] = []

    try:
        tree = ast.parse(content, filename=str(fpath))
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if _is_pass_only_body(node.body):
            kind = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            findings.append(
                f"pass-only function: {rel}:{node.lineno}: {kind} {node.name}()"
            )

    return findings


def _find_commented_code_blocks(fpath: Path) -> list[str]:
    """Find consecutive blocks of commented-out code."""
    content = read_file(fpath)
    if not content:
        return []

    rel = _rel(fpath)
    lines = content.split("\n")
    findings: list[str] = []

    consecutive = 0
    start = 0

    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("#") and _RE_COMMENTED_CODE.search(s):
            if consecutive == 0:
                start = i + 1
            consecutive += 1
        else:
            if consecutive >= COMMENT_BLOCK_MIN:
                findings.append(
                    f"commented-out code: {rel}:{start}-{start + consecutive}"
                )
            consecutive = 0

    # Check trailing block at EOF
    if consecutive >= COMMENT_BLOCK_MIN:
        findings.append(
            f"commented-out code: {rel}:{start}-{start + consecutive}"
        )

    return findings


def find_dead_code() -> list[str]:
    """Find pass-only functions and commented-out code blocks."""
    findings: list[str] = []

    for fpath in _discover_py_files():
        findings.extend(_find_pass_only_functions(fpath))
        findings.extend(_find_commented_code_blocks(fpath))

    return findings


# ── Placeholder Detection ─────────────────────────────────────────


def find_placeholders() -> list[str]:
    """Find NotImplementedError, TODO, FIXME, HACK, XXX, TBD, WIP, TEMP."""
    findings: list[str] = []

    for fpath in _discover_py_files():
        content = read_file(fpath)
        if not content:
            continue

        rel = _rel(fpath)

        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()

            if _RE_NOT_IMPL.search(stripped):
                findings.append(f"NotImplementedError: {rel}:{i}")

            m = _RE_PLACEHOLDER.search(stripped)
            if m:
                tag = m.group(1).upper()
                findings.append(f"{tag}: {rel}:{i}: {stripped[:80]}")

    return findings


# ── Stale File Detection (Git-based) ─────────────────────────────


def _git_last_commit_timestamp(fpath: Path) -> int | None:
    """Get the Unix timestamp of the last commit that touched fpath.

    Returns None if the file has no git history (new/untracked).
    """
    rel = str(fpath.relative_to(ROOT))
    code, out, _ = run_command(
        ["git", "log", "-1", "--format=%at", "--", rel],
    )
    if code != 0 or not out.strip():
        return None
    try:
        return int(out.strip())
    except ValueError:
        return None


def find_stale_files() -> list[str]:
    """Find tracked Python files not modified in STALE_DAYS days."""
    findings: list[str] = []
    now = int(time.time())
    cutoff = now - (STALE_DAYS * 86400)

    for fpath in _discover_py_files():
        if not fpath.exists():
            continue

        ts = _git_last_commit_timestamp(fpath)
        if ts is None:
            continue

        if ts < cutoff:
            age_days = (now - ts) // 86400
            findings.append(f"stale ({age_days}d): {_rel(fpath)}")

    findings.sort(key=lambda f: f.split("(")[1] if "(" in f else "", reverse=True)
    return findings


# ── Tech Debt Hotspots ────────────────────────────────────────────


def find_tech_debt_hotspots() -> list[str]:
    """Find files changed most frequently in recent history.

    Avoids duplicate counting within a single commit.
    """
    code, out, _ = run_command(
        ["git", "log", f"--max-count={HOTSPOT_HISTORY}",
         "--name-only", "--pretty=format:", "--"],
    )
    if code != 0 or not out.strip():
        return []

    # Deduplicate per commit
    current_commit_files: set[str] = set()
    all_commits: list[set[str]] = []

    for line in out.splitlines():
        stripped = line.strip()
        if not stripped:
            if current_commit_files:
                all_commits.append(current_commit_files)
                current_commit_files = set()
        elif stripped.endswith(".py"):
            current_commit_files.add(stripped.lstrip("./"))

    if current_commit_files:
        all_commits.append(current_commit_files)

    file_counts: Counter[str] = Counter()
    for commit_files in all_commits:
        for f in commit_files:
            file_counts[f] += 1

    findings: list[str] = []
    for f, count in sorted(
        file_counts.most_common(10),
        key=lambda x: (-x[1], x[0]),
    ):
        if count >= HOTSPOT_THRESHOLD:
            findings.append(f"hotspot ({count} recent changes): {f}")

    return findings


# ── Main ──────────────────────────────────────────────────────────


def run_hook() -> HookResult:
    """Run the repo health hook."""
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Dead code
    for f in find_dead_code():
        if "pass-only function" in f:
            errors.append(f)
        else:
            warnings.append(f)

    # 2. Placeholders
    for f in find_placeholders():
        if "NotImplementedError" in f:
            errors.append(f)
        else:
            warnings.append(f)

    # 3. Stale files
    for f in find_stale_files():
        warnings.append(f)

    # 4. Tech debt hotspots
    for f in find_tech_debt_hotspots():
        warnings.append(f)

    # Deduplicate
    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))

    total = len(errors) + len(warnings)

    return HookResult(
        name="Repo Health",
        passed=True,  # Health is informational, not blocking
        message=f"{len(errors)} issues, {len(warnings)} warnings",
        findings=errors + warnings[:MAX_FINDINGS],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
