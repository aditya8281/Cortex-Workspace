"""Validator — entity, relationship, and model-level validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.agents.integrity.model._base import EntityBase
from backend.app.agents.integrity.model.relationship_model import Relationship
from backend.app.agents.integrity.model import RepositoryKnowledgeModel


@dataclass
class ValidationError:
    field: str
    message: str


@dataclass
class ValidationResult:
    passed: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class Validator:
    """Validates entities, relationships, and full RKMs."""

    def validate_entity(self, entity: EntityBase) -> ValidationResult:
        errors: list[ValidationError] = []
        warnings: list[str] = []

        if not (0.0 <= entity.confidence <= 1.0):
            errors.append(
                ValidationError(
                    field="confidence",
                    message=(
                        f"confidence must be in [0, 1], got {entity.confidence}"
                    ),
                )
            )

        if not entity.source_collector:
            warnings.append("source_collector is empty")

        if not entity.source_version:
            warnings.append("source_version is empty")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_relationship(self, rel: Relationship) -> ValidationResult:
        errors: list[ValidationError] = []

        if not (0.0 <= rel.confidence <= 1.0):
            errors.append(
                ValidationError(
                    field="confidence",
                    message="confidence must be in [0, 1]",
                )
            )

        if rel.source_id == rel.target_id:
            errors.append(
                ValidationError(
                    field="target_id",
                    message=(
                        "self-referencing relationship "
                        "(source_id == target_id)"
                    ),
                )
            )

        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def validate_model(self, model: RepositoryKnowledgeModel) -> ValidationResult:
        errors: list[ValidationError] = []
        warnings: list[str] = []

        if not model.metadata.version:
            errors.append(
                ValidationError("version", "RKM version must not be empty")
            )

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
