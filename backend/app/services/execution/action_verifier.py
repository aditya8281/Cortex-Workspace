"""Pre-flight safety verification for tool executions."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any


class ActionVerifier:
    """Dangerous pattern detection, resource limit checks, custom rules."""

    DANGEROUS_PATTERNS: list[tuple[str, str, str]] = [
        (r"rm\s+-rf\s+/", "CRITICAL", "Recursive deletion of root filesystem"),
        (r"DROP\s+TABLE", "CRITICAL", "Database table deletion"),
        (r"DELETE\s+FROM.*WHERE\s+1", "CRITICAL", "Unconditional database deletion"),
        (r"sudo\s+", "HIGH", "Privilege escalation attempt"),
        (r"chmod\s+777", "HIGH", "Overly permissive file permissions"),
        (r">\s*/dev/sd", "CRITICAL", "Direct disk write"),
        (r"curl\s+.*\|\s*sh", "HIGH", "Remote code execution via pipe"),
        (r"eval\s*\(", "MEDIUM", "Dynamic code evaluation"),
        (r"exec\s*\(", "MEDIUM", "Dynamic code execution"),
        (r"__import__", "MEDIUM", "Dynamic module import"),
        (r"subprocess\.(call|run|Popen)", "MEDIUM", "Subprocess execution"),
        (r"os\.system\s*\(", "MEDIUM", "System command execution"),
        (r"\bpassword\b.*=", "LOW", "Potential password in parameters"),
        (r"\bsecret\b.*=", "LOW", "Potential secret in parameters"),
        (r"\bapi_key\b.*=", "LOW", "Potential API key in parameters"),
    ]

    RESOURCE_LIMITS: dict[str, int] = {
        "max_file_size_bytes": 100 * 1024 * 1024,
        "max_api_calls_per_minute": 60,
        "max_text_length": 1_000_000,
        "max_list_length": 10_000,
    }

    _SEVERITY_ORDER = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    def __init__(self) -> None:
        self._rules: list[dict[str, Any]] = []

    def add_rule(
        self,
        name: str,
        check_fn: Callable[..., Any],
        description: str,
        severity: str = "MEDIUM",
    ) -> None:
        self._rules.append(
            {
                "name": name,
                "check": check_fn,
                "description": description,
                "severity": severity,
            }
        )

    def add_dangerous_pattern(self, pattern: str, severity: str, description: str) -> None:
        self.DANGEROUS_PATTERNS.append((pattern, severity, description))

    def verify(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = context or {}
        warnings: list[str] = []
        errors: list[str] = []
        checks_performed: list[str] = []
        max_severity = "INFO"

        def update_severity(sev: str) -> None:
            nonlocal max_severity
            if self._SEVERITY_ORDER.get(sev, 0) > self._SEVERITY_ORDER.get(max_severity, 0):
                max_severity = sev

        # Dangerous patterns
        param_str = str(params)
        for pattern, severity, description in self.DANGEROUS_PATTERNS:
            if re.search(pattern, param_str, re.IGNORECASE):
                update_severity(severity)
                if severity in ("CRITICAL", "HIGH"):
                    errors.append(f"[{severity}] {description} (pattern: {pattern})")
                else:
                    warnings.append(f"[{severity}] {description} (pattern: {pattern})")
        checks_performed.append("dangerous_patterns")

        # Resource limits
        if (
            "text" in params
            and isinstance(params["text"], str)
            and len(params["text"]) > self.RESOURCE_LIMITS["max_text_length"]
        ):
            errors.append(f"Text length {len(params['text'])} exceeds limit {self.RESOURCE_LIMITS['max_text_length']}")
            update_severity("HIGH")
        checks_performed.append("resource_limits")

        if (
            "items" in params
            and isinstance(params["items"], list)
            and len(params["items"]) > self.RESOURCE_LIMITS["max_list_length"]
        ):
            errors.append(f"List length {len(params['items'])} exceeds limit {self.RESOURCE_LIMITS['max_list_length']}")
            update_severity("MEDIUM")
        checks_performed.append("list_limits")

        # Custom rules
        for rule in self._rules:
            try:
                result = rule["check"](tool_name, params, context)
                if result is False:
                    errors.append(f"Rule '{rule['name']}' failed: {rule['description']}")
                    update_severity(rule.get("severity", "MEDIUM"))
                elif result is True:
                    warnings.append(f"Rule '{rule['name']}' warning: {rule['description']}")
                checks_performed.append(f"rule:{rule['name']}")
            except Exception as e:
                warnings.append(f"Rule '{rule['name']}' error: {e!s}")
                checks_performed.append(f"rule:{rule['name']}:error")

        return {
            "approved": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "severity": max_severity,
            "tool_name": tool_name,
            "checks_performed": checks_performed,
        }
