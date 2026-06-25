"""RKM sub-models + RepositoryKnowledgeModel facade."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.agents.integrity.model.metadata_model import MetadataModel
from backend.app.agents.integrity.model.code_model import CodeModel
from backend.app.agents.integrity.model.ecosystem_model import EcosystemModel
from backend.app.agents.integrity.model.documentation_model import (
    DocumentationModel,
)
from backend.app.agents.integrity.model.relationship_model import (
    RelationshipModel,
)


@dataclass(frozen=True)
class RepositoryKnowledgeModel:
    metadata: MetadataModel
    code: CodeModel
    ecosystem: EcosystemModel
    documentation: DocumentationModel
    relationships: RelationshipModel
