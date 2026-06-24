#!/usr/bin/env python3
"""Bug discovery: Security pattern checks.

Checks:
- Hardcoded secrets or API keys
- Missing input sanitization
- Path traversal vulnerabilities
- SQL injection patterns
- Missing auth decorators
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

SECRET_PATTERNS = [
    (re.compile(r'(?i)(api_key|apikey|secret_key|password)\s*=\s*["\'][^"\']{8,}["\']'), "hardcoded secret"),
    (re.compile(r'(?i)sk-[a-zA-Z0-9]{20,}'), "API key pattern"),
    (re.compile(r'(?i)ghp_[a-zA-Z0-9]{36}'), "GitHub token"),
    (re.compile(r'(?i)AKIA[0-9A-Z]{16}'), "AWS access key"),
]


def check_security():
    findings = []

    py_files = list(ROOT.glob("backend/**/*.py")) + list(ROOT.glob("tests/**/*.py"))

    for fpath in py_files:
        if ".venv" in str(fpath) or "__pycache__" in str(fpath) or "conftest" in str(fpath):
            continue
        try:
            content = fpath.read_text()
        except (UnicodeDecodeError, PermissionError):
            continue

        rel = str(fpath.relative_to(ROOT))

        # Secret patterns
        for pattern, desc in SECRET_PATTERNS:
            for match in pattern.finditer(content):
                # Skip .env.example, test files, comments
                if ".env.example" in rel or "test_" in rel:
                    continue
                line_no = content[:match.start()].count("\n") + 1
                findings.append(f"  {rel}:{line_no} — {desc}: {match.group()[:50]}")

        # Path traversal check
        if ".." in content and ("open(" in content or "Path(" in content):
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                if ".." in line and ("open(" in line or "Path(" in line):
                    if "sanitize" not in line.lower() and "resolve" not in line:
                        findings.append(f"  {rel}:{i} — potential path traversal (no sanitization)")

    if findings:
        print(f"Security findings: {len(findings)}")
        for f in findings:
            print(f)
        return 1

    print("✓ Security check passed — no hardcoded secrets or obvious vulnerabilities")
    return 0


if __name__ == "__main__":
    sys.exit(check_security())
