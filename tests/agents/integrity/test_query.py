"""Tests for RepositoryQueryService."""

import uuid
from datetime import datetime, timezone

from backend.app.agents.integrity.query import RepositoryQueryService
from backend.app.agents.integrity.model import RepositoryKnowledgeModel
from backend.app.agents.integrity.model.metadata_model import (
    MetadataModel,
    RepositoryCapabilities,
)
from backend.app.agents.integrity.model.code_model import CodeModel
from backend.app.agents.integrity.model.ecosystem_model import EcosystemModel
from backend.app.agents.integrity.model.documentation_model import (
    DocumentationModel,
)
from backend.app.agents.integrity.model.relationship_model import (
    RelationshipModel,
)


def _make_empty_rkm() -> RepositoryKnowledgeModel:
    now = datetime.now(timezone.utc)
    return RepositoryKnowledgeModel(
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
        ecosystem=EcosystemModel(
            commands={}, skills={}, hooks={}, workflows={}, plans={}
        ),
        documentation=DocumentationModel(
            plans={}, source_of_truths={}, adrs=[]
        ),
        relationships=RelationshipModel(
            edges=[], relationship_schema_version="1.0"
        ),
    )


def test_query_find_by_id_none():
    q = RepositoryQueryService(_make_empty_rkm())
    assert q.find_by_id(uuid.uuid4()) is None


def test_query_find_routes_empty():
    q = RepositoryQueryService(_make_empty_rkm())
    assert q.find_routes() == []


def test_query_find_consumers_empty():
    q = RepositoryQueryService(_make_empty_rkm())
    assert q.find_consumers(uuid.uuid4()) == []


def test_query_find_producers_empty():
    q = RepositoryQueryService(_make_empty_rkm())
    assert q.find_producers(uuid.uuid4()) == []


def test_query_trace_empty():
    from backend.app.agents.integrity.model.relationship_model import (
        RelationshipType,
    )

    q = RepositoryQueryService(_make_empty_rkm())
    assert q.trace(uuid.uuid4(), [RelationshipType.IMPORTS]) == []


def test_query_find_dependencies_empty():
    q = RepositoryQueryService(_make_empty_rkm())
    assert q.find_dependencies(uuid.uuid4()) == []


def test_query_find_impact():
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()
    q = RepositoryQueryService(_make_empty_rkm())
    result = q.find_impact([id1, id2])
    assert len(result.directly_changed) == 2
    assert len(result.transitively_affected) == 0
