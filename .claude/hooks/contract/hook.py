#!/usr/bin/env python3
"""Hook 3 — Frontend/Backend Contract Hook

Trigger: API changes, schema changes, DTO changes, frontend API usage changes
Purpose: Verify endpoints exist, schemas match, no contract drift

Checks:
- Backend route definitions have response_model
- Frontend API calls match backend routes
- No orphaned routes
- No missing endpoints
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, print_result, read_file

# ── Compiled regex (once) ─────────────────────────────────────────

_RE_ROUTE = re.compile(
    r'@router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'
)
_RE_FETCH = re.compile(
    r'fetch\s*\(\s*[`"\']\/api\/v1\/([^`"\']+)[`"\']'
)
_RE_CLIENT_METHOD = re.compile(
    r'(?:get|post|put|patch|delete)\s*\(\s*[`"\']\/api\/v1\/([^`"\']+)[`"\']'
)
_RE_PARAM_TOKEN = re.compile(r'\$\{(\w+)\}')
_RE_PARAM_BRACE = re.compile(r'\{(\w+)\}')
_RE_PARAM_COLON = re.compile(r':\w+')
_RE_CAMEL_CASE = re.compile(r'(?<=[a-z0-9])(?=[A-Z])')
_RE_TEMPLATE_GARBAGE = re.compile(r'\$\{|encodeURIComponent|encodeURI\b|decodeURI|Math\.|window\.|qs[\s?\.]')

# ── Constants ─────────────────────────────────────────────────────

RESPONSE_MODEL_WINDOW = 200
MAX_FINDINGS = 15
ORPHANED_MAX = 10


# ── Backend Route Extraction ──────────────────────────────────────


def _check_has_response_model(content: str, decorator_end: int) -> bool:
    """Check if response_model is present in the decorator's argument list.

    Searches for matching parentheses from the decorator end position,
    rather than using a fixed window. This avoids false negatives from
    the old 500-char + first-`)` approach.
    """
    depth = 0
    start = decorator_end
    for i in range(decorator_end, min(decorator_end + 500, len(content))):
        ch = content[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth <= 0:
                decorator_args = content[start:i]
                return "response_model" in decorator_args
    window = content[decorator_end:decorator_end + RESPONSE_MODEL_WINDOW]
    return "response_model" in window


def extract_backend_routes() -> list[dict]:
    """Extract all backend route definitions."""
    routes: list[dict] = []
    api_dir = ROOT / "backend" / "app" / "api" / "v1"
    if not api_dir.exists():
        return routes

    for router_file in api_dir.glob("*.py"):
        if router_file.name.startswith("__"):
            continue
        try:
            content = read_file(router_file)
        except Exception:
            continue
        if not content:
            continue

        # Detect handler functions that return StreamingResponse or FileResponse
        # directly — these endpoints must NOT have response_model.
        streaming_funcs = set()
        _RE_NEXT_FUNC = re.compile(r'\n(?:async\s+)?def\s+')
        for sm in re.finditer(
            r'def\s+(\w+)\s*\(', content
        ):
            func_name = sm.group(1)
            if func_name.startswith('_'):
                continue
            # Check if function body contains a return of streaming types.
            # Split on the next function definition (sync or async) to isolate
            # just this function's body.
            func_body = content[sm.end():]
            next_func = _RE_NEXT_FUNC.search(func_body)
            body_text = func_body[:next_func.start()] if next_func else func_body
            if 'StreamingResponse(' in body_text or 'FileResponse(' in body_text:
                streaming_funcs.add(func_name)

        # Map decorator positions to function names by finding the first `def`
        # after each decorator.
        route_entries = list(_RE_ROUTE.finditer(content))
        for idx, match in enumerate(route_entries):
            method = match.group(1).upper()
            path = match.group(2)
            has_response = _check_has_response_model(content, match.end())
            # Find the def that follows this decorator (sync or async)
            next_def = re.search(r'\n(?:async\s+)?def\s+(\w+)\s*\(', content[match.end():])
            func_name = next_def.group(1) if next_def else ''
            is_streaming = func_name in streaming_funcs
            routes.append({
                "method": method,
                "path": path,
                "has_response_model": has_response,
                "is_streaming": is_streaming,
                "file": router_file.name,
            })
    return routes


# ── Frontend Call Extraction ──────────────────────────────────────


def extract_frontend_calls() -> list[dict]:
    """Extract all frontend API calls."""
    calls: list[dict] = []
    api_dir = ROOT / "frontend" / "src" / "shared" / "api"
    if not api_dir.exists():
        return calls

    for ts_file in api_dir.glob("*.ts"):
        if ts_file.name.startswith("__"):
            continue
        try:
            content = read_file(ts_file)
        except Exception:
            continue
        if not content:
            continue

        for match in _RE_FETCH.finditer(content):
            raw = match.group(1)
            if _is_clean_frontend_path(raw):
                calls.append({
                    "path": f"/api/v1/{raw}",
                    "file": ts_file.name,
                })
        for match in _RE_CLIENT_METHOD.finditer(content):
            raw = match.group(1)
            if _is_clean_frontend_path(raw):
                calls.append({
                    "path": f"/api/v1/{raw}",
                    "file": ts_file.name,
                })

    return calls


# ── Path Normalization ────────────────────────────────────────────


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case for path comparison."""
    return _RE_CAMEL_CASE.sub('_', name).lower()


def normalize_path(path: str) -> str:
    """Normalize API path for comparison.

    - Converts ${param} and {param} to :param
    - Converts camelCase param names to snake_case
    - Strips trailing slashes
    """
    normalized = _RE_PARAM_TOKEN.sub(r':\1', path)
    normalized = _RE_PARAM_BRACE.sub(r':\1', normalized)
    # Convert camelCase params to snake_case: :agentId → :agent_id
    parts = normalized.split('/')
    result_parts = []
    for part in parts:
        if part.startswith(':'):
            result_parts.append(':' + _camel_to_snake(part[1:]))
        else:
            result_parts.append(part)
    normalized = '/'.join(result_parts)
    return normalized.rstrip("/")


def _is_clean_frontend_path(raw: str) -> bool:
    """Check if a frontend path string is a clean API path (not template garbage)."""
    if _RE_TEMPLATE_GARBAGE.search(raw):
        return False
    if '${' in raw:
        return False
    return True


# ── Main Hook ─────────────────────────────────────────────────────


def run_hook() -> HookResult:
    """Run the contract hook."""
    try:
        backend_routes = extract_backend_routes()
    except Exception as exc:
        return HookResult(
            name="Contract Check",
            passed=False,
            message=f"Error extracting backend routes: {exc}",
        )

    try:
        frontend_calls = extract_frontend_calls()
    except Exception as exc:
        return HookResult(
            name="Contract Check",
            passed=False,
            message=f"Error extracting frontend calls: {exc}",
        )

    if not backend_routes and not frontend_calls:
        return HookResult(
            name="Contract Check",
            passed=True,
            message="No API routes or frontend calls found",
        )

    backend_paths: dict[str, dict] = {}
    for r in backend_routes:
        norm = normalize_path(r["path"])
        key = f"{r['method']} {norm}"
        backend_paths[key] = r

    frontend_paths: set[str] = set()
    for c in frontend_calls:
        norm = normalize_path(c["path"])
        frontend_paths.add(norm)

    findings: list[str] = []

    missing_model = [r for r in backend_routes if not r["has_response_model"] and not r.get("is_streaming", False)]
    for r in missing_model:
        findings.append(f"{r['file']}: {r['method']} {r['path']} — missing response_model")

    backend_norms = {normalize_path(r["path"]) for r in backend_routes}
    orphaned = backend_norms - frontend_paths
    system_routes = {
        "/health", "/docs", "/openapi.json", "/redoc",
        "/health/live", "/health/ready", "/health/deep",
        "/ws", "/ws/models", "/ws/system",
    }
    orphaned = orphaned - system_routes

    for path in sorted(orphaned)[:ORPHANED_MAX]:
        findings.append(f"Orphaned backend route (no frontend call): {path}")
    if len(orphaned) > ORPHANED_MAX:
        findings.append(f"... and {len(orphaned) - ORPHANED_MAX} more orphaned routes")

    missing = frontend_paths - backend_norms
    missing_filtered: set[str] = set()
    for m in missing:
        base = _RE_PARAM_COLON.sub('', m)
        has_similar = any(_RE_PARAM_COLON.sub('', bn) == base for bn in backend_norms)
        if not has_similar:
            missing_filtered.add(m)

    for path in sorted(missing_filtered):
        findings.append(f"Frontend calls non-existent route: {path}")

    warnings: list[str] = []
    if missing_model:
        warnings.append(f"{len(missing_model)} routes missing response_model")

    return HookResult(
        name="Contract Check",
        passed=len(findings) == 0,
        message=f"{len(findings)} contract issues" if findings else "Contract OK",
        findings=findings[:MAX_FINDINGS],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
