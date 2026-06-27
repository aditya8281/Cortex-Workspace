"""Data masking service — selective hiding of sensitive fields."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from typing import Any


class DataMaskingService:
    """Selective data masking for sensitive fields.

    Strategies:
    - full: "********" (fixed 8 chars)
    - partial: keeps first/last N chars, replaces middle with *
    - hash: truncated SHA-256 (deterministic, one-way)
    - redact: "[REDACTED]"
    """

    SENSITIVE_FIELDS = frozenset(
        {
            "password",
            "secret_key",
            "api_key",
            "token",
            "ssn",
            "credit_card",
            "private_key",
            "encryption_key",
            "master_key",
            "access_token",
        }
    )

    SENSITIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN"),
        (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "CARD"),
        (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "EMAIL"),
    ]

    def __init__(self) -> None:
        self._custom_strategies: dict[str, Callable[[str], str]] = {}

    def register_strategy(self, field_name: str, mask_fn: Callable[[str], str]) -> None:
        """Register a custom masking function for a specific field."""
        self._custom_strategies[field_name] = mask_fn

    def mask_field(
        self,
        value: str,
        strategy: str = "full",
        keep_first: int = 1,
        keep_last: int = 1,
    ) -> str:
        """Mask a single value using the specified strategy."""
        if not value:
            return value
        if strategy == "full":
            return "*" * min(len(value), 8)
        if strategy == "partial":
            if len(value) <= keep_first + keep_last:
                return "*" * len(value)
            return value[:keep_first] + "*" * (len(value) - keep_first - keep_last) + value[-keep_last:]
        if strategy == "hash":
            return hashlib.sha256(value.encode()).hexdigest()[:16]
        if strategy == "redact":
            return "[REDACTED]"
        return value

    def mask_dict(
        self,
        data: dict[str, Any],
        fields: list[str] | None = None,
        strategy: str = "full",
        keep_first: int = 1,
        keep_last: int = 1,
    ) -> dict[str, Any]:
        """Mask sensitive fields in a dictionary."""
        target_fields = fields if fields is not None else list(self.SENSITIVE_FIELDS)
        masked: dict[str, Any] = {}
        for key, value in data.items():
            if key in target_fields:
                if key in self._custom_strategies:
                    masked[key] = self._custom_strategies[key](str(value))
                else:
                    masked[key] = self.mask_field(str(value), strategy, keep_first, keep_last)
            elif isinstance(value, dict):
                masked[key] = self.mask_dict(value, target_fields, strategy, keep_first, keep_last)
            elif isinstance(value, list):
                masked[key] = [
                    self.mask_dict(item, target_fields, strategy, keep_first, keep_last)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                masked[key] = value
        return masked

    def mask_text(self, text: str) -> str:
        """Detect and mask sensitive patterns in free text."""
        result = text
        for pattern, label in self.SENSITIVE_PATTERNS:
            result = pattern.sub(f"[{label}]", result)
        return result
