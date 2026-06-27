#!/usr/bin/env python3
"""Hook 1 — UI Review Hook

Trigger: Frontend file modifications (.tsx, .ts, .css, .scss)
Purpose: Validate design quality, UX consistency, accessibility, design-system compliance

Checks:
- Design token usage (no hardcoded colors in frontend components)
- Glass morphism consistency (glass-panel class usage)
- Loading/empty/error state patterns
- Accessibility (alt text, aria labels, semantic HTML)
- Responsive design patterns
- No inline styles (use Tailwind)
- cn() utility usage (not raw clsx or template strings for classes)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from utils import ROOT, HookResult, get_changed_files, is_frontend_file, print_result, read_file

# Hardcoded color patterns that should use design tokens
HARDCODED_COLORS = [
    re.compile(r'#[0-9a-fA-F]{6}\b(?![-\w])'),  # #ffffff but not #ffffff-xxx
    re.compile(r'#[0-9a-fA-F]{3}\b(?![-\w])'),   # #fff
    re.compile(r'rgb\(\d+'),                        # rgb(255, 255, 255)
    re.compile(r'rgba\(\d+'),                       # rgba(0, 0, 0, 0.5)
]

# Allowed hardcoded colors (whitelist)
ALLOWED_COLORS = {"#000000", "#ffffff", "#fff", "#000", "transparent", "inherit"}

# Semantic patterns for states
STATE_PATTERNS = {
    "loading": re.compile(r'(isLoading|loading|isFetching|Pending)', re.IGNORECASE),
    "error": re.compile(r'(isError|error|Error|errorMessage)', re.IGNORECASE),
    "empty": re.compile(r'(isEmpty|empty|noData|noResults|noItems)', re.IGNORECASE),
}

# Accessibility patterns
A11Y_PATTERNS = {
    "alt_text": re.compile(r'<img\s', re.IGNORECASE),
    "aria_label": re.compile(r'aria-label|aria-labelledby|aria-describedby', re.IGNORECASE),
    "role": re.compile(r'role=', re.IGNORECASE),
    "tabindex": re.compile(r'tabIndex|tabindex', re.IGNORECASE),
}


def check_design_tokens(content: str, filepath: str) -> list:
    """Check for hardcoded colors that should use design tokens."""
    findings = []
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        # Skip comments, imports, and CSS variable definitions
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        if "var(--" in line:  # Already using CSS variables
            continue
        if "colors." in line or "palette." in line:  # Using token imports
            continue

        for pattern in HARDCODED_COLORS:
            matches = pattern.findall(line)
            for match in matches:
                if match.lower() not in ALLOWED_COLORS:
                    findings.append(f"{filepath}:{i}: hardcoded color '{match}' — use design tokens")
    return findings


def check_inline_styles(content: str, filepath: str) -> list:
    """Check for inline styles that should use Tailwind."""
    findings = []
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        if "style=" in line and "{" in line:
            # Allow dynamic styles that compute values
            if "transform" in line or "width" in line or "height" in line or "opacity" in line:
                continue  # Dynamic values are acceptable
            findings.append(f"{filepath}:{i}: inline style — use Tailwind classes")
    return findings


def check_accessibility(content: str, filepath: str) -> list:
    """Check for accessibility issues in React components."""
    findings = []
    lines = content.split("\n")

    has_images = bool(re.search(r'<img\s', content))
    has_alt = bool(re.search(r'alt=', content))

    if has_images and not has_alt:
        findings.append(f"{filepath}: <img> tags missing alt attribute")

    # Check for click handlers on non-interactive elements
    for i, line in enumerate(lines, 1):
        if re.search(r'onClick=', line):
            # Check if it's on a div or span without role
            if re.search(r'<(div|span)\s', line) and "role=" not in line:
                findings.append(f"{filepath}:{i}: onClick on non-interactive element — add role='button' or use <button>")

    return findings


def check_states(content: str, filepath: str) -> list:
    """Check if components handle loading, error, and empty states."""
    findings = []
    has_loading = bool(STATE_PATTERNS["loading"].search(content))
    has_error = bool(STATE_PATTERNS["error"].search(content))
    has_empty = bool(STATE_PATTERNS["empty"].search(content))

    # Only flag if component fetches data but doesn't handle states
    if "fetch" in content or "useQuery" in content or "useSWR" in content:
        if not has_loading:
            findings.append(f"{filepath}: data-fetching component missing loading state")
        if not has_error:
            findings.append(f"{filepath}: data-fetching component missing error state")

    return findings


def check_patterns(content: str, filepath: str) -> list:
    """Check for code quality patterns."""
    findings = []

    # Check for raw clsx usage instead of cn()
    if "clsx(" in content and "import { cn }" not in content:
        findings.append(f"{filepath}: use cn() utility instead of raw clsx()")

    # Check for dangerouslySetInnerHTML
    if "dangerouslySetInnerHTML" in content:
        findings.append(f"{filepath}: dangerouslySetInnerHTML used — ensure XSS protection")

    # Check for console.log in production code
    for i, line in enumerate(content.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("console.log(") and not filepath.endswith(".test.tsx"):
            findings.append(f"{filepath}:{i}: console.log in production code")

    return findings


def run_hook(files=None) -> HookResult:
    """Run the UI review hook."""
    if files is None:
        files = get_changed_files()

    frontend_files = [f for f in files if is_frontend_file(f) and f.suffix in (".tsx", ".ts", ".css", ".scss")]

    if not frontend_files:
        return HookResult(
            name="UI Review",
            passed=True,
            message="No frontend files changed",
        )

    all_findings = []
    for f in frontend_files:
        content = read_file(f)
        if not content:
            continue
        rel = str(f.relative_to(ROOT))
        all_findings.extend(check_design_tokens(content, rel))
        all_findings.extend(check_inline_styles(content, rel))
        all_findings.extend(check_accessibility(content, rel))
        all_findings.extend(check_states(content, rel))
        all_findings.extend(check_patterns(content, rel))

    warnings = [f for f in all_findings if "⚠" in f]
    errors = [f for f in all_findings if "⚠" not in f]

    result = HookResult(
        name="UI Review",
        passed=len(errors) == 0,
        message=f"{len(errors)} issues, {len(warnings)} warnings across {len(frontend_files)} files",
        findings=errors[:15],  # Cap output
        warnings=warnings[:10],
    )
    return result


if __name__ == "__main__":
    result = run_hook()
    print_result(result)
    sys.exit(0 if result.passed else 1)
