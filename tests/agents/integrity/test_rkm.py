"""Tests for RKM sub-models + RepositoryKnowledgeModel facade."""

from datetime import datetime, timezone

from backend.app.agents.integrity.model import RepositoryKnowledgeModel
from backend.app.agents.integrity.model.code_model import CodeModel
from backend.app.agents.integrity.model.documentation_model import (
    DocumentationModel,
)
from backend.app.agents.integrity.model.ecosystem_model import EcosystemModel
from backend.app.agents.integrity.model.metadata_model import (
    MetadataModel,
    RepositoryCapabilities,
)
from backend.app.agents.integrity.model.relationship_model import (
    RelationshipModel,
)


def test_metadata_model_version():
    mm = MetadataModel(
        version="1.0",
        relationship_schema_version="1.0",
        repository_hash="abc123",
        generated_at=datetime.now(timezone.utc),
        collector_versions={},
        capabilities=RepositoryCapabilities(),
    )
    assert mm.version == "1.0"
    assert mm.repository_hash == "abc123"


def test_repository_capabilities_defaults():
    rc = RepositoryCapabilities()
    assert len(rc.languages) == 0
    assert rc.has_frontend is False


def test_repository_capabilities_configured():
    rc = RepositoryCapabilities(
        languages={"python", "typescript"},
        frameworks={"fastapi"},
        has_backend=True,
    )
    assert "python" in rc.languages
    assert rc.has_backend is True


def test_code_model():
    cm = CodeModel(
        files={},
        directories=set(),
        symbols={},
        imports=[],
        schemas={},
        types={},
        routes={},
        routers={},
        middleware={},
        models={},
        migrations={},
        db_config=None,
        components={},
        api_clients={},
        configs={},
    )
    assert len(cm.files) == 0


def test_ecosystem_model():
    em = EcosystemModel(commands={}, skills={}, hooks={}, workflows={}, plans={})
    assert len(em.commands) == 0


def test_documentation_model():
    dm = DocumentationModel(plans={}, source_of_truths={}, adrs=[])
    assert len(dm.adrs) == 0


def test_rkm_facade():
    now = datetime.now(timezone.utc)
    rkm = RepositoryKnowledgeModel(
        metadata=MetadataModel(
            version="1.0",
            relationship_schema_version="1.0",
            repository_hash="abc",
            generated_at=now,
            collector_versions={},
            capabilities=RepositoryCapabilities(),
        ),
        code=CodeModel(
            files={},
            directories=set(),
            symbols={},
            imports=[],
            schemas={},
            types={},
            routes={},
            routers={},
            middleware={},
            models={},
            migrations={},
            db_config=None,
            components={},
            api_clients={},
            configs={},
        ),
        ecosystem=EcosystemModel(commands={}, skills={}, hooks={}, workflows={}, plans={}),
        documentation=DocumentationModel(plans={}, source_of_truths={}, adrs=[]),
        relationships=RelationshipModel(edges=[], relationship_schema_version="1.0"),
    )
    assert rkm.metadata.version == "1.0"
    assert rkm.relationships.relationship_schema_version == "1.0"
