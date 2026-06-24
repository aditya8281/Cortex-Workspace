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
from utils import ROOT, HookResult, get_changed_files, read_file, print_result


def extract_backend_routes():
    """Extract all backend route definitions."""
    routes = []
    api_dir = ROOT / "backend" / "app" / "api" / "v1"
    if not api_dir.exists():
        return routes

    for router_file in api_dir.glob("*.py"):
        content = read_file(router_file)
        if not content:
            continue

        pattern = r'@router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(pattern, content):
            method = match.group(1).upper()
            path = match.group(2)
            # Check if response_model is present
            pos = match.end()
            context = content[pos:pos + 500]
            has_response = "response_model" in context.split(")")[0] if context else False
            routes.append({
                "method": method,
                "path": path,
                "has_response_model": has_response,
                "file": router_file.name,
            })
    return routes


def extract_frontend_calls():
    """Extract all frontend API calls."""
    calls = []
    api_dir = ROOT / "frontend" / "src" / "shared" / "api"
    if not api_dir.exists():
        return calls

    for ts_file in api_dir.glob("*.ts"):
        content = read_file(ts_file)
        if not content:
            continue

        # Match fetch calls
        pattern = r'fetch\s*\(\s*[`"\']\/api\/v1\/([^`"\']+)[`"\']'
        for match in re.finditer(pattern, content):
            calls.append({
                "path": f"/api/v1/{match.group(1)}",
                "file": ts_file.name,
            })

        # Also match API client method calls like: get("/path"), post("/path")
        pattern2 = r'(?:get|post|put|patch|delete)\s*\(\s*[`"\']\/api\/v1\/([^`"\']+)[`"\']'
        for match in re.finditer(pattern2, content):
            calls.append({
                "path": f"/api/v1/{match.group(1)}",
                "file": ts_file.name,
            })

    return calls


def normalize_path(path: str) -> str:
    """Normalize API path for comparison (convert params to tokens)."""
    # Convert {param} and ${param} to :param
    normalized = re.sub(r'\$\{(\w+)\}', r':\1', path)
    normalized = re.sub(r'\{(\w+)\}', r':\1', normalized)
    # Remove trailing slashes
    normalized = normalized.rstrip("/")
    return normalized


def run_hook():
    """Run the contract hook."""
    backend_routes = extract_backend_routes()
    frontend_calls = extract_frontend_calls()

    if not backend_routes and not frontend_calls:
        return HookResult(
            name="Contract Check",
            passed=True,
            message="No API routes or frontend calls found",
        )

    # Normalize paths for comparison
    backend_paths = {}
    for r in backend_routes:
        norm = normalize_path(r["path"])
        key = f"{r['method']} {norm}"
        backend_paths[key] = r

    frontend_paths = set()
    for c in frontend_calls:
        norm = normalize_path(c["path"])
        frontend_paths.add(norm)

    findings = []

    # Check for routes missing response_model
    missing_model = [r for r in backend_routes if not r["has_response_model"]]
    if missing_model:
        for r in missing_model:
            findings.append(f"{r['file']}: {r['method']} {r['path']} — missing response_model")

    # Check for orphaned backend routes (not called by frontend)
    backend_norms = {normalize_path(r["path"]) for r in backend_routes}
    orphaned = backend_norms - frontend_paths
    # Filter out known system routes
    system_routes = {"/health", "/docs", "/openapi.json", "/redoc"}
    orphaned = orphaned - system_routes

    if orphaned:
        for path in sorted(orphaned):
            findings.append(f"Orphaned backend route (no frontend call): {path}")

    # Check for frontend calls to non-existent routes
    # More lenient: frontend may call routes with different param styles
    missing = frontend_paths - backend_norms
    # Filter out dynamic routes (frontend might use different param names)
    missing_filtered = set()
    for m in missing:
        # Check if a similar route exists (with different param names)
        base = re.sub(r':\w+', '', m)
        has_similar = any(re.sub(r':\w+', '', bn) == base for bn in backend_norms)
        if not has_similar:
            missing_filtered.add(m)

    if missing_filtered:
        for path in sorted(missing_filtered):
            findings.append(f"Frontend calls non-existent route: {path}")

    warnings = []
    if missing_model:
        warnings.append(f"{len(missing_model)} routes missing response_model")

    return HookResult(
        name="Contract Check",
        passed=len(findings) == 0,
        message=f"{len(findings)} contract issues" if findings else "Contract OK",
        findings=findings[:15],
        warnings=warnings,
    )


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
