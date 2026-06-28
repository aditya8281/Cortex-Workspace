"""Error analysis service with fingerprinting and pattern matching."""

from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.cognition.error_analysis import ErrorAnalysis

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Severity classification rules
# ---------------------------------------------------------------------------
SEVERITY_MAP: dict[str, str] = {
    "SecurityError": "critical",
    "DataCorruptionError": "critical",
    "EncryptionError": "critical",
    "ValueError": "error",
    "TypeError": "error",
    "RuntimeError": "error",
    "IOError": "error",
    "DeprecationWarning": "warning",
    "ResourceWarning": "warning",
    "TimeoutError": "warning",
    "UserWarning": "info",
    "SyntaxWarning": "info",
}
DEFAULT_SEVERITY = "info"

# ---------------------------------------------------------------------------
# Resolution pattern templates:  {ErrorType}:{pattern_key}  ->  resolution
# ---------------------------------------------------------------------------
RESOLUTION_PATTERNS: dict[str, str] = {
    "SecurityError:encrypt": "Verify encryption keys and re-encrypt the data with correct keys",
    "SecurityError:auth": "Check authentication credentials and refresh tokens",
    "SecurityError:permission": "Review access permissions and ensure proper authorization",
    "DataCorruptionError:checksum": "Restore data from backup and verify checksums",
    "DataCorruptionError:format": "Re-parse data with correct format specification",
    "EncryptionError:decrypt": "Verify decryption key and re-download or regenerate data",
    "ValueError:invalid": "Validate input parameters against expected range and format",
    "ValueError:type": "Ensure the correct data type is provided for the operation",
    "ValueError:parse": "Check input format and use appropriate parser",
    "TypeError:convert": "Use explicit type conversion with proper error handling",
    "TypeError:argument": "Check function signature and provide correct argument types",
    "RuntimeError:timeout": "Increase timeout or optimize the operation for faster execution",
    "RuntimeError:resource": "Free up system resources and retry the operation",
    "IOError:file": "Verify file exists and has correct permissions",
    "IOError:network": "Check network connectivity and retry the operation",
    "DeprecationWarning:api": "Update to the latest API version and migrate deprecated calls",
    "TimeoutError:connection": "Check network and server status, retry with backoff",
    "TimeoutError:operation": "Optimize operation performance or increase timeout threshold",
}

# Keywords to extract from an error message for resolution matching.
PATTERN_KEYWORDS = [
    "encrypt",
    "decrypt",
    "auth",
    "permission",
    "checksum",
    "format",
    "invalid",
    "type",
    "parse",
    "convert",
    "argument",
    "timeout",
    "resource",
    "file",
    "network",
    "api",
    "connection",
    "operation",
]


class ErrorAnalysisService:
    """Error analysis with fingerprinting, severity classification, and
    pattern-driven resolution suggestions.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_error(
        self,
        user_id: int,
        error_type: str,
        error_message: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ErrorAnalysis:
        """Full analysis pipeline: fingerprint, severity, root cause, resolution."""
        fingerprint = self._generate_fingerprint(error_type, error_message or "")
        severity = self._classify_severity(error_type)
        ctx = context or {}
        similar = self._find_similar_errors(fingerprint, user_id)
        root_cause = self._determine_root_cause(error_type, error_message or "", ctx, similar)
        resolution = self._suggest_resolution(error_type, error_message or "", similar)
        prevention = self._suggest_prevention(error_type, similar)
        related_id = similar[0].id if similar else None

        analysis = ErrorAnalysis(
            user_id=user_id,
            error_type=error_type,
            error_message=error_message,
            fingerprint=fingerprint,
            context=ctx,
            root_cause=root_cause,
            resolution=resolution,
            prevention=prevention,
            severity=severity,
            related_analysis_id=related_id,
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_error_patterns(self, user_id: int, days: int = 30) -> list[dict[str, Any]]:
        """Return common error patterns with counts and severity breakdown."""
        since = datetime.utcnow() - timedelta(days=days)
        errors = (
            self.db.query(ErrorAnalysis)
            .filter(ErrorAnalysis.user_id == user_id, ErrorAnalysis.created_at >= since)
            .all()
        )

        groups: dict[str, dict[str, Any]] = {}
        for err in errors:
            fp = err.fingerprint or f"{err.error_type}:unknown"
            if fp not in groups:
                groups[fp] = {
                    "fingerprint": fp,
                    "error_type": err.error_type,
                    "count": 0,
                    "severity_counts": Counter(),
                    "last_seen": err.created_at,
                }
            groups[fp]["count"] += 1
            groups[fp]["severity_counts"][err.severity] += 1
            if err.created_at and (groups[fp]["last_seen"] is None or err.created_at > groups[fp]["last_seen"]):
                groups[fp]["last_seen"] = err.created_at

        sorted_groups = sorted(groups.values(), key=lambda g: g["count"], reverse=True)

        result: list[dict[str, Any]] = []
        for group in sorted_groups:
            fp_errors = [e for e in errors if (e.fingerprint or f"{e.error_type}:unknown") == group["fingerprint"]]
            trend = self._calculate_trend(fp_errors)
            result.append(
                {
                    "fingerprint": group["fingerprint"],
                    "error_type": group["error_type"],
                    "count": group["count"],
                    "severity_breakdown": dict(group["severity_counts"]),
                    "last_seen": group["last_seen"],
                    "trend": trend,
                }
            )
        return result

    def resolve_error(self, analysis_id: int, resolution_method: str = "manual") -> ErrorAnalysis:
        """Mark an analysis record as resolved."""
        analysis = self._get_analysis_or_raise(analysis_id)
        analysis.resolved = 1
        analysis.resolution_method = resolution_method
        analysis.resolved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_analysis(self, analysis_id: int) -> ErrorAnalysis | None:
        """Return a single analysis by ID."""
        return self.db.query(ErrorAnalysis).filter(ErrorAnalysis.id == analysis_id).first()

    def get_user_analyses(
        self,
        user_id: int,
        severity: str | None = None,
        limit: int = 50,
    ) -> list[ErrorAnalysis]:
        """Return analyses for a user, optionally filtered by severity."""
        query = self.db.query(ErrorAnalysis).filter(ErrorAnalysis.user_id == user_id)
        if severity:
            query = query.filter(ErrorAnalysis.severity == severity)
        query = query.order_by(ErrorAnalysis.created_at.desc()).limit(limit)
        return query.all()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_analysis_or_raise(self, analysis_id: int) -> ErrorAnalysis:
        analysis = self.db.query(ErrorAnalysis).filter(ErrorAnalysis.id == analysis_id).first()
        if analysis is None:
            raise ValueError(f"Analysis {analysis_id} not found")
        return analysis

    def _generate_fingerprint(self, error_type: str, message: str) -> str:
        """Normalise an error message by replacing volatile parts with wildcards.

        Order matters: UUIDs are matched *before* raw numbers so that
        hex segments like ``550e8400`` are not converted to ``{num}`` first.
        """
        normalized = message[:100]
        # Long-form patterns first (before short ones steal their tokens).
        normalized = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{uuid}",
            normalized,
            flags=re.IGNORECASE,
        )
        normalized = re.sub(r"https?://\S+", "{url}", normalized)
        normalized = re.sub(r"/[a-zA-Z0-9_./-]+", "{path}", normalized)
        normalized = re.sub(r"\b\d+\b", "{num}", normalized)
        normalized = re.sub(r"\s+", "_", normalized.strip())
        return f"{error_type}:{normalized[:100]}"

    def _classify_severity(self, error_type: str) -> str:
        return SEVERITY_MAP.get(error_type, DEFAULT_SEVERITY)

    def _find_similar_errors(self, fingerprint: str, user_id: int, limit: int = 10) -> list[ErrorAnalysis]:
        return (
            self.db.query(ErrorAnalysis)
            .filter(
                ErrorAnalysis.fingerprint == fingerprint,
                ErrorAnalysis.user_id == user_id,
            )
            .order_by(ErrorAnalysis.created_at.desc())
            .limit(limit)
            .all()
        )

    def _determine_root_cause(
        self,
        error_type: str,
        message: str,
        context: dict[str, Any],
        similar_errors: list[ErrorAnalysis],
    ) -> str:
        """Derive root cause from historical correlation, falling back to type-based heuristics."""
        # Prefer the most common historical root cause.
        causes = [e.root_cause for e in similar_errors if e.root_cause]
        if causes:
            return Counter(causes).most_common(1)[0][0]

        type_causes: dict[str, str] = {
            "SecurityError": "Unauthorized access attempt detected",
            "DataCorruptionError": "Data integrity check failed",
            "EncryptionError": "Encryption/decryption operation failed",
            "ValueError": "Invalid value provided for operation",
            "TypeError": "Type mismatch in operation",
            "RuntimeError": "Runtime execution failure",
            "IOError": "Input/output operation failure",
            "TimeoutError": "Operation exceeded time limit",
            "DeprecationWarning": "Deprecated API or feature in use",
        }
        return type_causes.get(error_type, f"Unhandled {error_type} occurred")

    def _suggest_resolution(
        self,
        error_type: str,
        message: str,
        similar_errors: list[ErrorAnalysis],
    ) -> str:
        """Suggest resolution from pattern templates or historical resolutions."""
        key = f"{error_type}:{self._extract_pattern_key(message)}"
        if key in RESOLUTION_PATTERNS:
            return RESOLUTION_PATTERNS[key]

        # Fallback to the most common historical resolution.
        resolutions = [e.resolution for e in similar_errors if e.resolution]
        if resolutions:
            return Counter(resolutions).most_common(1)[0][0]

        return f"Investigate the {error_type} and apply appropriate corrective action"

    def _suggest_prevention(self, error_type: str, similar_errors: list[ErrorAnalysis]) -> str:
        """Suggest prevention from historical data or heuristics."""
        preventions = [e.prevention for e in similar_errors if e.prevention]
        if preventions:
            return Counter(preventions).most_common(1)[0][0]

        type_prevention: dict[str, str] = {
            "SecurityError": "Implement proper authentication and authorization checks",
            "DataCorruptionError": "Add data validation and integrity checks before processing",
            "EncryptionError": "Ensure encryption keys are properly managed and rotated",
            "ValueError": "Add input validation with clear error messages",
            "TypeError": "Use type checking and explicit type conversion",
            "RuntimeError": "Add comprehensive error handling and logging",
            "TimeoutError": "Implement timeout handling with retry logic",
            "IOError": "Add file/network availability checks before operations",
        }
        return type_prevention.get(error_type, "Add defensive programming and error handling practices")

    def _calculate_trend(self, errors: list[ErrorAnalysis]) -> str:
        """Classify frequency as *increasing*, *decreasing*, or *stable*."""
        if len(errors) < 3:
            return "stable"

        sorted_errors = sorted(errors, key=lambda e: e.created_at or datetime.min)
        mid = len(sorted_errors) // 2
        first_half = sorted_errors[:mid]
        second_half = sorted_errors[mid:]

        if len(second_half) > len(first_half) * 1.2:
            return "increasing"
        elif len(first_half) > len(second_half) * 1.2:
            return "decreasing"
        return "stable"

    def _extract_pattern_key(self, message: str) -> str:
        """Pick the first matching keyword from the message for pattern lookup."""
        msg_lower = message.lower()
        for kw in PATTERN_KEYWORDS:
            if kw in msg_lower:
                return kw
        return "unknown"
