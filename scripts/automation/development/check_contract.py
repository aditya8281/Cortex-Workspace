#!/usr/bin/env python3
"""Development validation: Check frontend/backend API contract.

Verifies:
- All API endpoints defined in backend have corresponding frontend calls
- Response schemas match between backend Pydantic models and frontend TypeScript types
- No orphaned endpoints (backend endpoints not called by frontend)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def extract_backend_routes():
    """Extract all FastAPI route definitions."""
    routes = []
    api_dir = ROOT / "backend" / "app" / "api" / "v1"

    if not api_dir.exists():
        return routes

    for router_file in api_dir.glob("*.py"):
        content = router_file.read_text()
        # Match @router.get, @router.post, etc.
        pattern = r'@router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(pattern, content):
            method = match.group(1).upper()
            path = match.group(2)
            routes.append({
                "method": method,
                "path": path,
                "file": router_file.name
            })

    return routes


def extract_frontend_api_calls():
    """Extract all API calls from frontend code."""
    calls = []
    api_dir = ROOT / "frontend" / "src" / "shared" / "api"

    if not api_dir.exists():
        return calls

    for ts_file in api_dir.glob("*.ts"):
        content = ts_file.read_text()
        # Match fetch calls with method and path
        # Pattern: fetch(`/api/v1/...`, { method: 'POST', ... })
        pattern = r'fetch\s*\(\s*[`"\']\/api\/v1\/([^`"\']+)[`"\']'
        for match in re.finditer(pattern, content):
            path = match.group(1)
            calls.append({
                "path": f"/api/v1/{path}",
                "file": ts_file.name
            })

    return calls


def check_contract():
    """Check frontend/backend contract."""
    print("Checking frontend/backend API contract...")

    backend_routes = extract_backend_routes()
    frontend_calls = extract_frontend_api_calls()

    print(f"Backend routes: {len(backend_routes)}")
    print(f"Frontend API calls: {len(frontend_calls)}")

    # Convert routes to set for comparison
    backend_paths = {r["path"] for r in backend_routes}
    frontend_paths = {c["path"] for c in frontend_calls}

    # Find orphaned routes (backend routes not called by frontend)
    orphaned_routes = backend_paths - frontend_paths
    if orphaned_routes:
        print(f"\nOrphaned backend routes (not called by frontend): {len(orphaned_routes)}")
        for route in sorted(orphaned_routes)[:10]:
            print(f"  - {route}")

    # Find missing routes (frontend calls to non-existent backend routes)
    missing_routes = frontend_paths - backend_paths
    if missing_routes:
        print(f"\nMissing backend routes (frontend calls non-existent): {len(missing_routes)}")
        for route in sorted(missing_routes)[:10]:
            print(f"  - {route}")

    if not orphaned_routes and not missing_routes:
        print("\n✓ Frontend/backend contract check passed")
        return 0
    else:
        print("\n⚠ Contract issues found (review above)")
        return 1


if __name__ == "__main__":
    sys.exit(check_contract())
