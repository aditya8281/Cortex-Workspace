"""Aggregator + Reporter — aggregate findings, produce Markdown/JSON output."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from backend.app.agents.integrity.model.finding import Finding


@dataclass
class AggregateResult:
    total_findings: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_classification: dict[str, int] = field(default_factory=dict)


class Aggregator:
    """Aggregate findings into summary metrics."""

    def aggregate(self, findings: list[Finding]) -> AggregateResult:
        by_severity: dict[str, int] = {}
        by_classification: dict[str, int] = {}

        for f in findings:
            sev = (
                f.severity.name
                if hasattr(f.severity, "name")
                else str(f.severity)
            )
            cls_ = (
                f.classification.name
                if hasattr(f.classification, "name")
                else str(f.classification)
            )
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_classification[cls_] = by_classification.get(cls_, 0) + 1

        return AggregateResult(
            total_findings=len(findings),
            by_severity=by_severity,
            by_classification=by_classification,
        )


class Reporter:
    """Produce human-readable and machine-readable reports."""

    def to_markdown(
        self,
        findings: list[Finding],
        metrics: AggregateResult,
    ) -> str:
        lines = [
            "# Integrity Report",
            "",
            "## Summary",
            "",
            f"- Total findings: {metrics.total_findings}",
            "",
            "### By Severity",
        ]
        for sev, count in sorted(
            metrics.by_severity.items(), reverse=True
        ):
            lines.append(f"- **{sev}**: {count}")

        lines.extend(["", "### By Classification"])
        for cls_, count in sorted(metrics.by_classification.items()):
            lines.append(f"- {cls_}: {count}")

        lines.extend(["", "## Findings"])
        for f in findings:
            sev_name = (
                f.severity.name
                if hasattr(f.severity, "name")
                else str(f.severity)
            )
            cls_name = (
                f.classification.name
                if hasattr(f.classification, "name")
                else str(f.classification)
            )
            lines.extend(
                [
                    "",
                    f"### {sev_name}: {f.title}",
                    f"- Location: {f.location}",
                    f"- Classification: {cls_name}",
                    f"- {f.description}",
                ]
            )

        return "\n".join(lines)

    def to_json(
        self,
        findings: list[Finding],
        metrics: AggregateResult,
    ) -> str:
        data = {
            "summary": {
                "total_findings": metrics.total_findings,
                "by_severity": metrics.by_severity,
                "by_classification": metrics.by_classification,
            },
            "findings": [
                {
                    "title": f.title,
                    "severity": (
                        f.severity.name
                        if hasattr(f.severity, "name")
                        else str(f.severity)
                    ),
                    "classification": (
                        f.classification.name
                        if hasattr(f.classification, "name")
                        else str(f.classification)
                    ),
                    "location": f.location,
                    "description": f.description,
                }
                for f in findings
            ],
        }
        return json.dumps(data, indent=2)
