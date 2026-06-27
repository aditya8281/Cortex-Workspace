from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field


class RelationshipDirection(enum.Enum):
    DIRECTED = "directed"
    BIDIRECTIONAL = "bidirectional"
    TRANSITIVE = "transitive"


class Multiplicity(enum.Enum):
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_MANY = "N:N"


class EdgeStrength(enum.Enum):
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"


class RelationshipType(enum.Enum):
    IMPORTS = "imports"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    RETURNS = "returns"
    ACCEPTS = "accepts"
    SERIALIZES = "serializes"
    DESERIALIZES = "deserializes"
    DEPENDS_ON = "depends_on"
    PRODUCES = "produces"
    CONSUMES = "consumes"
    REFERENCES = "references"
    DOCUMENTS = "documents"
    EXTENDS = "extends"
    MIGRATES_TO = "migrates_to"
    CONFIGURES = "configures"
    OWNS = "owns"
    TESTS = "tests"
    VALIDATES = "validates"


@dataclass(frozen=True)
class Relationship:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    type: RelationshipType = RelationshipType.REFERENCES
    direction: RelationshipDirection = RelationshipDirection.DIRECTED
    multiplicity: Multiplicity = Multiplicity.ONE_TO_ONE
    strength: EdgeStrength = EdgeStrength.MEDIUM
    source_id: uuid.UUID = field(default_factory=uuid.uuid4)
    target_id: uuid.UUID = field(default_factory=uuid.uuid4)
    metadata: dict[str, str] | None = None
    confidence: float = 1.0
    source_collector: str = "unknown"


@dataclass(frozen=True)
class RelationshipModel:
    edges: list[Relationship] = field(default_factory=list)
    relationship_schema_version: str = "1.0"
