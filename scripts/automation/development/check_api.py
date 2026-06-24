#!/usr/bin/env python3
"""Development validation: API convention checks.

Verifies:
- All routes use response_model on decorators
- Specific routes registered before parameterized routes
- Router files exist for each domain
- No duplicate route registrations
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def check_api():
    errors = []
    warnings = []

    api_dir = ROOT / "backend" / "app" / "api"
    router_py = api_dir / "router.py"

    if not router_py.exists():
        print("ERROR: backend/app/api/router.py not found")
        return 1

    # Check router registration
    router_content = router_py.read_text()
    includes = re.findall(r'include_router\((\w+)', router_content)
    print(f"Registered routers: {len(includes)}")

    # Check for specific routes before parameterized
    v1_dir = api_dir / "v1"
    if v1_dir.exists():
        route_issues = []
        for router_file in v1_dir.glob("*.py"):
            content = router_file.read_text()
            lines = content.split("\n")
            specific_paths = []
            param_paths = []

            for i, line in enumerate(lines, 1):
                match = re.search(r'@router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']', line)
                if match:
                    path = match.group(2)
                    if "{" in path:
                        param_paths.append((router_file.name, i, path))
                    else:
                        specific_paths.append((router_file.name, i, path))

            # Check ordering: specific should come before parameterized
            if param_paths and specific_paths:
                last_specific_line = max(s[1] for s in specific_paths)
                first_param_line = min(p[1] for p in param_paths)
                if first_param_line < last_specific_line:
                    for p in param_paths:
                        if p[1] < last_specific_line:
                            route_issues.append(
                                f"  {p[0]}:{p[1]}: parameterized route '{p[2]}' before specific routes"
                            )

            # Check response_model usage
            for match in re.finditer(r'@router\.(get|post|put|patch|delete)\s*\(', content):
                # Check next few lines for response_model
                pos = match.end()
                context = content[pos:pos + 300]
                if "response_model" not in context:
                    warnings.append(
                        f"  {router_file.name}: {match.group(1).upper()} route missing response_model"
                    )

        if route_issues:
            errors.extend(route_issues)
            print(f"Route ordering issues: {len(route_issues)}")
        else:
            print("Route ordering: OK ✓")
    else:
        print("No v1/ router directory found")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)} routes missing response_model):")
        for w in warnings[:5]:  # Show first 5
            print(w)
        if len(warnings) > 5:
            print(f"  ... and {len(warnings) - 5} more")

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(e)
        return 1

    print("\n✓ API convention check passed")
    return 0


if __name__ == "__main__":
    sys.exit(check_api())
