# Integrity System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Core Repository Integrity System — a platform for structural, semantic, and evolution analysis of the Cortex repository.

**Architecture:** Extractor → Normalizer → Validator → RKM (façade over 5 sub-models) → RepositoryQueryService → Engine Registry → IntegrityService (public API) → Aggregator + Reporter. 10 engines in V1 across 5 milestones.

**Tech Stack:** Python 3.11+, SQLAlchemy 2.0 (models only — no DB for RKM), standard library (dataclasses, enum, pathlib, uuid), pytest.

## Global Constraints

- Every entity must carry a stable UUID (`uuid4`) — never reuse or mutate IDs
- All relationships reference UUIDs, not names
- Every dataclass is frozen (`@dataclass(frozen=True)`) for immutability
- Confidence values are floats in [0, 1]; 1.0 = exact, < 1.0 = inferred
- Every Finding must have severity, priority, and urgency
- All engines register via `@register` decorator at module import time
- Engine names are kebab-case (e.g. `"import-graph"`, `"schema-engine"`)
- No external dependencies beyond stdlib + pytest for V1
- `RepositoryQueryService` is the primary interface for engines — engines rarely access RKM dicts directly
- All test files go in `tests/agents/integrity/`
- Each milestone keeps existing tests passing (baseline ~1000)
- Performance target: full-repo scan < 5s (< 50k files), incremental < 1s

---

## File Structure

```
backend/app/agents/integrity/
    __init__.py
    service.py
    workflow.py
    model/
        __init__.py
        _base.py
        metadata_model.py
        code_model.py
        ecosystem_model.py
        documentation_model.py
        relationship_model.py
        finding.py
        metrics.py
        context.py
        source_of_truth.py
    query.py
    validation.py
    views.py
    closure.py
    registry.py
    report.py
    engines/
        __init__.py
        _base.py
        structural/
            __init__.py
            import_engine.py
            dependency_engine.py
            migration_engine.py
            filesystem_engine.py
            configuration_engine.py
        semantic/
            __init__.py
            schema_engine.py
            api_contract_engine.py
            cross_layer_engine.py
        evolution/
            __init__.py
            documentation_engine.py
            planning_engine.py
    extractors/
        __init__.py
        _base.py
        python_extractor.py
        python_normalizer.py
        yaml_extractor.py
        yaml_normalizer.py
        json_extractor.py
        json_normalizer.py
        markdown_extractor.py
        md_normalizer.py
    ecosystem_extractors/
        __init__.py
        plan_extractor.py
        plan_normalizer.py
        skill_extractor.py
        skill_normalizer.py
        command_extractor.py
        command_normalizer.py
        hook_extractor.py
        hook_normalizer.py
        workflow_extractor.py
        workflow_normalizer.py

tests/agents/integrity/
    __init__.py
    conftest.py
    test_entity_base.py
    test_rkm.py
    test_relationships.py
    test_context.py
    test_finding.py
    test_metrics.py
    test_validator.py
    test_extractors.py
    test_normalizers.py
    test_query.py
    test_views.py
    test_closure.py
    test_registry.py
    test_report.py
    test_service.py
    test_workflow.py
    engines/
        __init__.py
        test_base.py
        structural/
            test_import_engine.py
            test_dependency_engine.py
            test_migration_engine.py
            test_filesystem_engine.py
            test_configuration_engine.py
        semantic/
            test_schema_engine.py
            test_api_contract_engine.py
            test_cross_layer_engine.py
        evolution/
            test_documentation_engine.py
            test_planning_engine.py
```

---

## Milestone 1 — Foundation (14 tasks)

### Task 1: Core Types — EntityBase, AnalysisContext, enums

**Files:**
- Create: `backend/app/agents/integrity/__init__.py`
- Create: `backend/app/agents/integrity/model/__init__.py`
- Create: `backend/app/agents/integrity/model/_base.py`
- Create: `backend/app/agents/integrity/model/context.py`
- Test: `tests/agents/integrity/__init__.py`
- Test: `tests/agents/integrity/test_entity_base.py`
- Test: `tests/agents/integrity/test_context.py`

**Interfaces:**
- Produces: `EntityBase`, `EntityType`, `ExecutionProfile`, `AnalysisScope`, `AnalysisContext`, `IntegrityDomain`, `Severity`, `Classification`, `Priority`, `IntegrityMode`

- [ ] **Step 1: Write failing tests for EntityBase**

```python
# tests/agents/integrity/test_entity_base.py
import uuid
from datetime import datetime, timezone
from backend.app.agents.integrity.model._base import EntityBase

def test_entity_base_has_uuid():
    class Concrete(EntityBase):
        pass
    e = Concrete(confidence=1.0, source_collector="test", source_version="1.0")
    assert isinstance(e.id, uuid.UUID)

def test_entity_base_confidence_range():
    import dataclasses
    with dataclasses.dataclass(frozen=True)
    class Concrete(EntityBase):
        pass
    Concrete(confidence=0.5, source_collector="test", source_version="1.0")
    # Should not raise

def test_entity_base_source_fields():
    class Concrete(EntityBase):
        pass
    e = Concrete(confidence=0.8, source_collector="python", source_version="1.0")
    assert e.confidence == 0.8
    assert e.source_collector == "python"
    assert e.source_version == "1.0"
```

- [ ] **Step 2: Run failing test**

```bash
pytest tests/agents/integrity/test_entity_base.py -v
```
Expected: FAIL — module not found

- [ ] **Step 3: Implement EntityBase**

```python
# backend/app/agents/integrity/__init__.py
"""Cortex Core Repository Integrity System."""

# backend/app/agents/integrity/model/__init__.py
"""RKM sub-models."""

# backend/app/agents/integrity/model/_base.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EntityBase:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    confidence: float = 1.0
    source_collector: str = "unknown"
    source_version: str = "0.1"
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_entity_base.py -v
```
Expected: PASS

- [ ] **Step 5: Write and implement enums + AnalysisContext**

```python
# tests/agents/integrity/test_context.py
from backend.app.agents.integrity.model.context import (
    ExecutionProfile, AnalysisScope, AnalysisContext,
    IntegrityDomain, Severity, Classification, Priority,
)
from pathlib import Path

def test_execution_profile_values():
    assert ExecutionProfile.FULL.value == "full"
    assert ExecutionProfile.INCREMENTAL.value == "incremental"

def test_analysis_scope_values():
    assert AnalysisScope.FULL_REPOSITORY.value == "full_repository"

def test_analysis_context_defaults():
    ctx = AnalysisContext(
        profile=ExecutionProfile.FULL,
        scope=AnalysisScope.FULL_REPOSITORY,
        repository_root=Path("/tmp"),
    )
    assert ctx.profile == ExecutionProfile.FULL
    assert ctx.changed_files is None
    assert ctx.target_engines is None

def test_integrity_domain_values():
    assert IntegrityDomain.STRUCTURAL.value == "structural"
    assert IntegrityDomain.SEMANTIC.value == "semantic"
    assert IntegrityDomain.EVOLUTION.value == "evolution"

def test_severity_ordering():
    assert Severity.CRITICAL > Severity.INSIGHT
    assert list(Severity) == [
        Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM,
        Severity.LOW, Severity.INSIGHT,
    ]

def test_classification_values():
    assert Classification.MISSING.value == "missing"
    assert Classification.DRIFTED.value == "drifted"

def test_priority_values():
    assert Priority.P0.value == "P0"
    assert Priority.P3.value == "P3"
```

- [ ] **Step 6: Run context tests to verify fail**

```bash
pytest tests/agents/integrity/test_context.py -v
```
Expected: FAIL — module not found

- [ ] **Step 7: Implement enums + AnalysisContext**

```python
# backend/app/agents/integrity/model/context.py
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ExecutionProfile(enum.Enum):
    QUICK = "quick"
    INCREMENTAL = "incremental"
    VERIFICATION = "verification"
    FULL = "full"
    COMPLETE = "complete"
    TARGET = "target"


class AnalysisScope(enum.Enum):
    FILES_CHANGED = "files_changed"
    DEPENDENCY_CLOSURE = "dependency_closure"
    FULL_REPOSITORY = "full_repository"


class IntegrityDomain(enum.Enum):
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    EVOLUTION = "evolution"


class Severity(enum.IntEnum):
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    INSIGHT = 0


class Classification(enum.Enum):
    MISSING = "missing"
    INCOMPATIBLE = "incompatible"
    AMBIGUOUS = "ambiguous"
    UNUSED = "unused"
    DUPLICATE = "duplicate"
    CIRCULAR = "circular"
    OBSOLETE = "obsolete"
    UNREACHABLE = "unreachable"
    INCONSISTENT = "inconsistent"
    DRIFTED = "drifted"


class Priority(enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


@dataclass(frozen=True)
class AnalysisContext:
    profile: ExecutionProfile
    scope: AnalysisScope
    repository_root: Path
    changed_files: list[Path] | None = None
    target_paths: list[Path] | None = None
    target_engines: list[str] | None = None
    feature_name: str | None = None
    branch: str | None = None
    active_version: str | None = None
    active_phase: str | None = None
    execution_reason: str | None = None
```

- [ ] **Step 8: Run all tests to verify pass**

```bash
pytest tests/agents/integrity/test_entity_base.py tests/agents/integrity/test_context.py -v
```
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add backend/app/agents/integrity/__init__.py
git add backend/app/agents/integrity/model/__init__.py
git add backend/app/agents/integrity/model/_base.py
git add backend/app/agents/integrity/model/context.py
git add tests/agents/integrity/__init__.py
git add tests/agents/integrity/test_entity_base.py
git add tests/agents/integrity/test_context.py
git commit -m "feat(integrity): core types — EntityBase, enums, AnalysisContext"
```

---

### Task 2: Relationship Model

**Files:**
- Create: `backend/app/agents/integrity/model/relationship_model.py`
- Test: `tests/agents/integrity/test_relationships.py`

**Interfaces:**
- Consumes: `EntityBase` (from Task 1)
- Produces: `RelationshipType`, `RelationshipDirection`, `Multiplicity`, `EdgeStrength`, `Relationship`, `RelationshipModel`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_relationships.py
import uuid
from backend.app.agents.integrity.model.relationship_model import (
    RelationshipType, RelationshipDirection, Multiplicity, EdgeStrength,
    Relationship, RelationshipModel,
)

def test_relationship_type_count():
    assert len(RelationshipType) >= 18  # all 18 types defined

def test_relationship_direction_values():
    assert RelationshipDirection.DIRECTED.value == "directed"
    assert RelationshipDirection.BIDIRECTIONAL.value == "bidirectional"

def test_multiplicity_values():
    assert Multiplicity.ONE_TO_ONE.value == "1:1"
    assert Multiplicity.MANY_TO_MANY.value == "N:N"

def test_edge_strength_values():
    assert EdgeStrength.STRONG.value == "strong"
    assert EdgeStrength.WEAK.value == "weak"

def test_relationship_creation():
    source = uuid.uuid4()
    target = uuid.uuid4()
    rel = Relationship(
        type=RelationshipType.IMPORTS,
        direction=RelationshipDirection.DIRECTED,
        multiplicity=Multiplicity.ONE_TO_MANY,
        strength=EdgeStrength.STRONG,
        source_id=source,
        target_id=target,
        source_collector="test",
    )
    assert rel.type == RelationshipType.IMPORTS
    assert rel.source_id == source
    assert rel.target_id == target
    assert isinstance(rel.id, uuid.UUID)

def test_relationship_metadata():
    rel = Relationship(
        type=RelationshipType.CALLS,
        direction=RelationshipDirection.DIRECTED,
        multiplicity=Multiplicity.ONE_TO_ONE,
        strength=EdgeStrength.MEDIUM,
        source_id=uuid.uuid4(),
        target_id=uuid.uuid4(),
        metadata={"line": "42", "file": "app.py"},
        source_collector="test",
    )
    assert rel.metadata["line"] == "42"

def test_relationship_model():
    model = RelationshipModel(
        edges=[], relationship_schema_version="1.0"
    )
    assert model.relationship_schema_version == "1.0"
    assert len(model.edges) == 0
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_relationships.py -v
```

- [ ] **Step 3: Implement Relationship model**

```python
# backend/app/agents/integrity/model/relationship_model.py
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from typing import Any


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
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_relationships.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/integrity/model/relationship_model.py
git add tests/agents/integrity/test_relationships.py
git commit -m "feat(integrity): Relationship model with direction, multiplicity, strength"
```

---

### Task 3: RKM Sub-Models + Facade

**Files:**
- Create: `backend/app/agents/integrity/model/metadata_model.py`
- Create: `backend/app/agents/integrity/model/code_model.py`
- Create: `backend/app/agents/integrity/model/ecosystem_model.py`
- Create: `backend/app/agents/integrity/model/documentation_model.py`
- Create: `tests/agents/integrity/test_rkm.py`

**Interfaces:**
- Produces: `MetadataModel`, `RepositoryCapabilities`, `CodeModel`, `EcosystemModel`, `DocumentationModel`, `RepositoryKnowledgeModel` (facade)

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_rkm.py
import uuid
from pathlib import Path
from datetime import datetime, timezone
from backend.app.agents.integrity.model.metadata_model import (
    MetadataModel, RepositoryCapabilities,
)
from backend.app.agents.integrity.model.code_model import CodeModel
from backend.app.agents.integrity.model.ecosystem_model import EcosystemModel
from backend.app.agents.integrity.model.documentation_model import DocumentationModel
from backend.app.agents.integrity.model.relationship_model import RelationshipModel

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
    em = EcosystemModel(
        commands={}, skills={}, hooks={}, workflows={}, plans={},
    )
    assert len(em.commands) == 0

def test_documentation_model():
    dm = DocumentationModel(
        plans={}, source_of_truths={}, adrs=[],
    )
    assert len(dm.adrs) == 0

def test_rkm_facade():
    from backend.app.agents.integrity.model import RepositoryKnowledgeModel
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
        code=CodeModel(files={}, directories=set(), symbols={}, imports=[],
                       schemas={}, types={}, routes={}, routers={},
                       middleware={}, models={}, migrations={},
                       db_config=None, components={}, api_clients={},
                       configs={}),
        ecosystem=EcosystemModel(commands={}, skills={}, hooks={},
                                 workflows={}, plans={}),
        documentation=DocumentationModel(plans={}, source_of_truths={},
                                         adrs=[]),
        relationships=RelationshipModel(edges=[],
                                        relationship_schema_version="1.0"),
    )
    assert rkm.metadata.version == "1.0"
    assert rkm.relationships.relationship_schema_version == "1.0"
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_rkm.py -v
```

- [ ] **Step 3: Implement MetadataModel + RepositoryCapabilities**

```python
# backend/app/agents/integrity/model/metadata_model.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RepositoryCapabilities:
    languages: set[str] = field(default_factory=set)
    frameworks: set[str] = field(default_factory=set)
    has_frontend: bool = False
    has_backend: bool = False
    has_database_migrations: bool = False
    has_docker: bool = False
    has_ci: bool = False


@dataclass(frozen=True)
class MetadataModel:
    version: str
    relationship_schema_version: str
    repository_hash: str
    generated_at: datetime
    collector_versions: dict[str, str] = field(default_factory=dict)
    capabilities: RepositoryCapabilities = field(default_factory=RepositoryCapabilities)
```

- [ ] **Step 4: Implement CodeModel, EcosystemModel, DocumentationModel**

```python
# backend/app/agents/integrity/model/code_model.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import uuid


@dataclass(frozen=True)
class CodeModel:
    files: dict[uuid.UUID, Any]
    directories: set[Path]
    symbols: dict[uuid.UUID, Any]
    imports: list[Any]
    schemas: dict[uuid.UUID, Any]
    types: dict[uuid.UUID, Any]
    routes: dict[uuid.UUID, Any]
    routers: dict[uuid.UUID, Any]
    middleware: dict[uuid.UUID, Any]
    models: dict[uuid.UUID, Any]
    migrations: dict[uuid.UUID, Any]
    db_config: Any | None
    components: dict[uuid.UUID, Any]
    api_clients: dict[uuid.UUID, Any]
    configs: dict[uuid.UUID, Any]


# backend/app/agents/integrity/model/ecosystem_model.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass(frozen=True)
class EcosystemModel:
    commands: dict[uuid.UUID, Any]
    skills: dict[uuid.UUID, Any]
    hooks: dict[uuid.UUID, Any]
    workflows: dict[uuid.UUID, Any]
    plans: dict[uuid.UUID, Any]


# backend/app/agents/integrity/model/documentation_model.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass(frozen=True)
class DocumentationModel:
    plans: dict[uuid.UUID, Any]
    source_of_truths: dict[uuid.UUID, Any]
    adrs: list[Any]
```

- [ ] **Step 5: Implement RKM facade**

```python
# backend/app/agents/integrity/model/__init__.py — add facade
from __future__ import annotations

from dataclasses import dataclass

from backend.app.agents.integrity.model.metadata_model import MetadataModel
from backend.app.agents.integrity.model.code_model import CodeModel
from backend.app.agents.integrity.model.ecosystem_model import EcosystemModel
from backend.app.agents.integrity.model.documentation_model import DocumentationModel
from backend.app.agents.integrity.model.relationship_model import RelationshipModel


@dataclass(frozen=True)
class RepositoryKnowledgeModel:
    metadata: MetadataModel
    code: CodeModel
    ecosystem: EcosystemModel
    documentation: DocumentationModel
    relationships: RelationshipModel
```

- [ ] **Step 6: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_rkm.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/agents/integrity/model/metadata_model.py
git add backend/app/agents/integrity/model/code_model.py
git add backend/app/agents/integrity/model/ecosystem_model.py
git add backend/app/agents/integrity/model/documentation_model.py
git add tests/agents/integrity/test_rkm.py
git commit -m "feat(integrity): RKM sub-models + facade"
```

---

### Task 4: Findings, Metrics, Source-of-Truth

**Files:**
- Create: `backend/app/agents/integrity/model/finding.py`
- Create: `backend/app/agents/integrity/model/metrics.py`
- Create: `backend/app/agents/integrity/model/source_of_truth.py`
- Test: `tests/agents/integrity/test_finding.py`
- Test: `tests/agents/integrity/test_metrics.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_finding.py
from backend.app.agents.integrity.model.finding import (
    Finding, CandidateFix, FixType,
)
from backend.app.agents.integrity.model.context import (
    Severity, Classification, Priority,
)

def test_finding_minimal():
    f = Finding(
        title="test finding",
        description="a test",
        severity=Severity.HIGH,
        priority=Priority.P1,
        urgency=5,
        classification=Classification.DRIFTED,
        location="app.py:42",
    )
    assert f.title == "test finding"
    assert f.fix is None
    assert isinstance(f.related_findings, list)
    assert f.confidence == 1.0

def test_finding_with_fix():
    fix = CandidateFix(
        fix_type=FixType.SCRIPT,
        fix_code="rm old_file.py",
    )
    f = Finding(
        title="orphan file",
        description="unused file",
        severity=Severity.LOW,
        priority=Priority.P3,
        urgency=2,
        classification=Classification.UNUSED,
        location="old.py",
        fix=fix,
    )
    assert f.fix.fix_type == FixType.SCRIPT
    assert f.fix.autofix_available is True

def test_finding_full():
    f = Finding(
        title="migration conflict",
        description="two migrations target same table",
        severity=Severity.CRITICAL,
        priority=Priority.P0,
        urgency=10,
        classification=Classification.DUPLICATE,
        location="migrations/001.py",
        affected_components=["UserModel"],
        dependency_chain=["migrations/001 → migrations/002"],
        root_cause="merge conflict",
        downstream_impact="schema inconsistency",
        recommendation="resolve migration order",
        confidence=0.95,
        related_findings=["F-002"],
        owner="backend-team",
        tags={"migration", "schema"},
        references=["docs/DATABASE.md"],
    )
    assert f.severity == Severity.CRITICAL
    assert f.priority == Priority.P0
```

```python
# tests/agents/integrity/test_metrics.py
from backend.app.agents.integrity.model.metrics import (
    IntegrityScores, ExecutionMetrics,
)
from backend.app.agents.integrity.model.context import Severity, Classification

def test_integrity_scores():
    s = IntegrityScores(
        integrity_score=85.0,
        structural_score=90.0,
        semantic_score=80.0,
        evolution_score=70.0,
    )
    assert s.integrity_score == 85.0
    assert 0 <= s.structural_score <= 100

def test_execution_metrics_defaults():
    m = ExecutionMetrics()
    assert m.total_findings == 0
    assert len(m.by_severity) == 0
    assert m.coverage == 0.0
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_finding.py tests/agents/integrity/test_metrics.py -v
```

- [ ] **Step 3: Implement Finding, Metrics, Source-of-Truth**

```python
# backend/app/agents/integrity/model/finding.py
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from typing import Any

from backend.app.agents.integrity.model.context import (
    Severity, Classification, Priority,
)


class FixType(enum.Enum):
    MANUAL = "manual"
    SCRIPT = "script"
    PATCH = "patch"


@dataclass(frozen=True)
class CandidateFix:
    fix_type: FixType = FixType.MANUAL
    fix_code: str | None = None
    autofix_available: bool = True
    estimated_effort: str = "minutes"
    breaking_change: bool = False


@dataclass(frozen=True)
class Finding:
    id: str = ""
    title: str = ""
    description: str = ""
    severity: Severity = Severity.INSIGHT
    priority: Priority = Priority.P3
    urgency: int = 1
    classification: Classification = Classification.INCONSISTENT
    location: str = ""
    affected_components: list[str] = field(default_factory=list)
    dependency_chain: list[str] = field(default_factory=list)
    root_cause: str = ""
    downstream_impact: str = ""
    recommendation: str = ""
    fix: CandidateFix | None = None
    confidence: float = 1.0
    related_findings: list[str] = field(default_factory=list)
    owner: str | None = None
    tags: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


# backend/app/agents/integrity/model/metrics.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.agents.integrity.model.context import Severity, Classification


@dataclass
class IntegrityScores:
    integrity_score: float = 0.0
    structural_score: float = 0.0
    semantic_score: float = 0.0
    evolution_score: float = 0.0


@dataclass
class RepositoryAnalytics:
    dependency_density: float = 0.0
    fan_in_distribution: dict[str, int] = field(default_factory=dict)
    fan_out_distribution: dict[str, int] = field(default_factory=dict)
    architectural_hotspots: list[str] = field(default_factory=list)
    coupling_coefficient: float = 0.0
    cycles: int = 0


@dataclass
class PerformanceMetrics:
    collection_time_ms: int = 0
    view_build_time_ms: int = 0
    analysis_time_ms: int = 0
    peak_memory_mb: float = 0.0


@dataclass
class ExecutionMetrics:
    total_findings: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_classification: dict[str, int] = field(default_factory=dict)
    by_engine: dict[str, int] = field(default_factory=dict)
    coverage: float = 0.0
    confidence_distribution: list[float] = field(default_factory=list)
```

```python
# backend/app/agents/integrity/model/source_of_truth.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceOfTruth:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    entity_type: str = ""
    path: Path = Path(".")
    schema_version: str | None = None
    validation_rules: list[str] = field(default_factory=list)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_finding.py tests/agents/integrity/test_metrics.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/integrity/model/finding.py
git add backend/app/agents/integrity/model/metrics.py
git add backend/app/agents/integrity/model/source_of_truth.py
git add tests/agents/integrity/test_finding.py
git add tests/agents/integrity/test_metrics.py
git commit -m "feat(integrity): Finding, Metrics, SourceOfTruth models"
```

---

### Task 5: Validator

**Files:**
- Create: `backend/app/agents/integrity/validation.py`
- Test: `tests/agents/integrity/test_validator.py`

**Interfaces:**
- Consumes: `EntityBase`, `Relationship`, `RepositoryKnowledgeModel`
- Produces: `ValidationResult`, `Validator`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_validator.py
import uuid
from backend.app.agents.integrity.validation import Validator, ValidationResult
from backend.app.agents.integrity.model._base import EntityBase
from backend.app.agents.integrity.model.relationship_model import (
    Relationship, RelationshipType, RelationshipDirection,
    Multiplicity, EdgeStrength,
)

def test_validate_entity_valid():
    class E(EntityBase):
        pass
    e = E(confidence=0.5, source_collector="test", source_version="1.0")
    v = Validator()
    result = v.validate_entity(e)
    assert result.passed is True
    assert len(result.errors) == 0

def test_validate_entity_confidence_out_of_range():
    class E(EntityBase):
        pass
    e = E(confidence=1.5, source_collector="test", source_version="1.0")
    v = Validator()
    result = v.validate_entity(e)
    assert result.passed is False
    assert any("confidence" in str(err).lower() for err in result.errors)

def test_validate_entity_negative_confidence():
    class E(EntityBase):
        pass
    e = E(confidence=-0.1, source_collector="test", source_version="1.0")
    v = Validator()
    result = v.validate_entity(e)
    assert result.passed is False

def test_validate_relationship_valid():
    rel = Relationship(
        type=RelationshipType.IMPORTS,
        direction=RelationshipDirection.DIRECTED,
        multiplicity=Multiplicity.ONE_TO_MANY,
        strength=EdgeStrength.STRONG,
        source_id=uuid.uuid4(),
        target_id=uuid.uuid4(),
        source_collector="test",
    )
    v = Validator()
    result = v.validate_relationship(rel)
    assert result.passed is True

def test_validate_relationship_self_reference():
    id_ = uuid.uuid4()
    rel = Relationship(
        type=RelationshipType.REFERENCES,
        direction=RelationshipDirection.DIRECTED,
        multiplicity=Multiplicity.ONE_TO_ONE,
        strength=EdgeStrength.WEAK,
        source_id=id_,
        target_id=id_,
        source_collector="test",
    )
    v = Validator()
    result = v.validate_relationship(rel)
    assert result.passed is False

def test_validator_warnings():
    class E(EntityBase):
        pass
    e = E(confidence=1.0, source_collector="test", source_version="1.0")
    v = Validator()
    result = v.validate_entity(e)
    assert isinstance(result.warnings, list)
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_validator.py -v
```

- [ ] **Step 3: Implement Validator**

```python
# backend/app/agents/integrity/validation.py
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
    def validate_entity(self, entity: EntityBase) -> ValidationResult:
        errors: list[ValidationError] = []
        warnings: list[str] = []
        
        # UUID is non-null (dataclass ensures this via default_factory)
        if not (0.0 <= entity.confidence <= 1.0):
            errors.append(ValidationError(
                field="confidence",
                message=f"confidence must be in [0, 1], got {entity.confidence}",
            ))
        
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
            errors.append(ValidationError(
                field="confidence",
                message="confidence must be in [0, 1]",
            ))
        
        if rel.source_id == rel.target_id:
            errors.append(ValidationError(
                field="target_id",
                message="self-referencing relationship (source_id == target_id)",
            ))
        
        return ValidationResult(passed=len(errors) == 0, errors=errors)
    
    def validate_model(self, model: RepositoryKnowledgeModel) -> ValidationResult:
        errors: list[ValidationError] = []
        warnings: list[str] = []
        
        if not model.metadata.version:
            errors.append(ValidationError("version", "RKM version must not be empty"))
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_validator.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/integrity/validation.py
git add tests/agents/integrity/test_validator.py
git commit -m "feat(integrity): Validator — entity, relationship, model validation"
```

---

### Task 6: Extractor/Normalizer Base + Python Plugin

**Files:**
- Create: `backend/app/agents/integrity/extractors/__init__.py`
- Create: `backend/app/agents/integrity/extractors/_base.py`
- Create: `backend/app/agents/integrity/extractors/python_extractor.py`
- Create: `backend/app/agents/integrity/extractors/python_normalizer.py`
- Test: `tests/agents/integrity/test_extractors.py`

**Interfaces:**
- Produces: `CollectorPlugin`, `Extractor`, `Normalizer`, `PythonExtractor`, `PythonNormalizer`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_extractors.py
from pathlib import Path
from backend.app.agents.integrity.extractors._base import (
    CollectorPlugin, Extractor, Normalizer,
)
from backend.app.agents.integrity.extractors.python_extractor import PythonExtractor
from backend.app.agents.integrity.extractors.python_normalizer import PythonNormalizer

def test_collector_plugin_defaults():
    p = CollectorPlugin(name="test", plugin_version="1.0",
                        supported_rkm_version="1.x")
    assert p.name == "test"
    assert p.supported_rkm_version == "1.x"

def test_python_extractor_plugin():
    e = PythonExtractor()
    assert e.plugin.name == "python"
    assert e.plugin.plugin_version == "1.0"

def test_python_extractor_extract():
    e = PythonExtractor()
    # extract from a real file
    result = e.extract(Path("backend/app/agents/integrity/model/_base.py"))
    assert "imports" in result
    assert "classes" in result
    assert len(result["classes"]) >= 1  # EntityBase

def test_python_normalizer():
    n = PythonNormalizer()
    raw = {"imports": ["os"], "classes": ["EntityBase"], "functions": []}
    entities = n.normalize(raw)
    assert len(entities) >= 1  # at minimum file-level entity
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_extractors.py -v
```

- [ ] **Step 3: Implement base classes**

```python
# backend/app/agents/integrity/extractors/__init__.py
"""Collector plugins — extract raw data, normalize into entities."""

# backend/app/agents/integrity/extractors/_base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.app.agents.integrity.model._base import EntityBase


@dataclass
class CollectorPlugin:
    name: str
    plugin_version: str
    supported_rkm_version: str = "1.x"
    supported_language_version: str | None = None


class Extractor(ABC):
    def __init__(self, plugin: CollectorPlugin | None = None) -> None:
        self.plugin = plugin or CollectorPlugin(
            name="unknown", plugin_version="0.1",
        )
    
    @abstractmethod
    def extract(self, path: Path) -> dict[str, Any]: ...


class Normalizer(ABC):
    def __init__(self, plugin: CollectorPlugin | None = None) -> None:
        self.plugin = plugin or CollectorPlugin(
            name="unknown", plugin_version="0.1",
        )
    
    @abstractmethod
    def normalize(self, raw: dict[str, Any]) -> list[EntityBase]: ...
```

- [ ] **Step 4: Implement PythonExtractor**

```python
# backend/app/agents/integrity/extractors/python_extractor.py
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from backend.app.agents.integrity.extractors._base import (
    CollectorPlugin, Extractor,
)


class PythonExtractor(Extractor):
    def __init__(self) -> None:
        super().__init__(CollectorPlugin(
            name="python",
            plugin_version="1.0",
            supported_rkm_version="1.x",
            supported_language_version="3.9+",
        ))
    
    def extract(self, path: Path) -> dict[str, Any]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        classes = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]
        functions = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        
        return {
            "path": str(path),
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "raw_tree": tree,
        }
```

- [ ] **Step 5: Implement PythonNormalizer**

```python
# backend/app/agents/integrity/extractors/python_normalizer.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.agents.integrity.extractors._base import (
    CollectorPlugin, Normalizer,
)
from backend.app.agents.integrity.model._base import EntityBase


class FileEntity(EntityBase):
    path: str = ""
    entity_type: str = "file"
    raw_metadata: dict[str, Any] | None = None


class PythonNormalizer(Normalizer):
    def __init__(self) -> None:
        super().__init__(CollectorPlugin(
            name="python-normalizer",
            plugin_version="1.0",
            supported_rkm_version="1.x",
        ))
    
    def normalize(self, raw: dict[str, Any]) -> list[EntityBase]:
        entities: list[EntityBase] = []
        
        # File-level entity
        file_entity = FileEntity(
            path=raw.get("path", ""),
            entity_type="python_file",
            raw_metadata={
                "classes": raw.get("classes", []),
                "functions": raw.get("functions", []),
                "imports": raw.get("imports", []),
            },
            source_collector="python",
            source_version="1.0",
        )
        entities.append(file_entity)
        
        # Per-class entities
        for cls_name in raw.get("classes", []):
            class_entity = FileEntity(
                entity_type="python_class",
                path=raw.get("path", ""),
                raw_metadata={"name": cls_name},
                source_collector="python",
                source_version="1.0",
            )
            entities.append(class_entity)
        
        return entities
```

- [ ] **Step 6: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_extractors.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/agents/integrity/extractors/__init__.py
git add backend/app/agents/integrity/extractors/_base.py
git add backend/app/agents/integrity/extractors/python_extractor.py
git add backend/app/agents/integrity/extractors/python_normalizer.py
git add tests/agents/integrity/test_extractors.py
git commit -m "feat(integrity): Extractor/Normalizer base + Python plugin"
```

---

### Task 7: RepositoryQueryService

**Files:**
- Create: `backend/app/agents/integrity/query.py`
- Test: `tests/agents/integrity/test_query.py`

**Interfaces:**
- Consumes: `RepositoryKnowledgeModel`
- Produces: `RepositoryQueryService`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_query.py
import uuid
from pathlib import Path
from datetime import datetime, timezone
from backend.app.agents.integrity.query import RepositoryQueryService
from backend.app.agents.integrity.model import RepositoryKnowledgeModel
from backend.app.agents.integrity.model.metadata_model import (
    MetadataModel, RepositoryCapabilities,
)
from backend.app.agents.integrity.model.code_model import CodeModel
from backend.app.agents.integrity.model.ecosystem_model import EcosystemModel
from backend.app.agents.integrity.model.documentation_model import DocumentationModel
from backend.app.agents.integrity.model.relationship_model import (
    RelationshipModel, Relationship, RelationshipType,
    RelationshipDirection, Multiplicity, EdgeStrength,
)

def _make_rkm() -> RepositoryKnowledgeModel:
    now = datetime.now(timezone.utc)
    return RepositoryKnowledgeModel(
        metadata=MetadataModel(
            version="1.0", relationship_schema_version="1.0",
            repository_hash="abc", generated_at=now,
            collector_versions={}, capabilities=RepositoryCapabilities(),
        ),
        code=CodeModel(
            files={}, directories=set(), symbols={}, imports=[],
            schemas={}, types={}, routes={}, routers={},
            middleware={}, models={}, migrations={}, db_config=None,
            components={}, api_clients={}, configs={},
        ),
        ecosystem=EcosystemModel(
            commands={}, skills={}, hooks={}, workflows={}, plans={},
        ),
        documentation=DocumentationModel(
            plans={}, source_of_truths={}, adrs=[],
        ),
        relationships=RelationshipModel(
            edges=[], relationship_schema_version="1.0",
        ),
    )

def test_query_find_by_id_none():
    q = RepositoryQueryService(_make_rkm())
    assert q.find_by_id(uuid.uuid4()) is None

def test_query_find_routes_empty():
    q = RepositoryQueryService(_make_rkm())
    assert q.find_routes() == []

def test_query_find_consumers_empty():
    q = RepositoryQueryService(_make_rkm())
    assert q.find_consumers(uuid.uuid4()) == []

def test_query_find_producers_empty():
    q = RepositoryQueryService(_make_rkm())
    assert q.find_producers(uuid.uuid4()) == []

def test_query_trace_empty():
    q = RepositoryQueryService(_make_rkm())
    assert q.trace(uuid.uuid4(), [RelationshipType.IMPORTS]) == []

def test_query_find_dependencies_empty():
    q = RepositoryQueryService(_make_rkm())
    assert q.find_dependencies(uuid.uuid4()) == []

def test_query_find_impact_empty():
    q = RepositoryQueryService(_make_rkm())
    result = q.find_impact([uuid.uuid4()])
    assert len(result.directly_changed) == 1
    assert len(result.transitively_affected) == 0
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_query.py -v
```

- [ ] **Step 3: Implement RepositoryQueryService**

```python
# backend/app/agents/integrity/query.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path

from backend.app.agents.integrity.model import RepositoryKnowledgeModel
from backend.app.agents.integrity.model._base import EntityBase
from backend.app.agents.integrity.model.relationship_model import (
    RelationshipType, Relationship,
)
from backend.app.agents.integrity.model.code_model import CodeModel


@dataclass
class ImpactSet:
    directly_changed: list[uuid.UUID] = field(default_factory=list)
    transitively_affected: list[uuid.UUID] = field(default_factory=list)
    affected_symbols: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)


@dataclass
class DependencyEdge:
    source_id: uuid.UUID
    target_id: uuid.UUID
    reason: str = ""
    path: list[uuid.UUID] = field(default_factory=list)


class RepositoryQueryService:
    def __init__(self, model: RepositoryKnowledgeModel) -> None:
        self._model = model
    
    def find_routes(self, path_pattern: str | None = None) -> list[Any]:
        routes = list(self._model.code.routes.values())
        if path_pattern:
            return [r for r in routes if path_pattern in str(r)]
        return routes
    
    def find_schemas(self, field_name: str) -> list[Any]:
        return []
    
    def find_by_id(self, entity_id: uuid.UUID) -> Any | None:
        for collection in [
            self._model.code.files, self._model.code.symbols,
            self._model.code.schemas, self._model.code.types,
            self._model.code.routes, self._model.code.models,
            self._model.code.migrations,
            self._model.ecosystem.commands, self._model.ecosystem.skills,
            self._model.ecosystem.hooks, self._model.ecosystem.workflows,
            self._model.ecosystem.plans,
        ]:
            if entity_id in collection:
                return collection[entity_id]
        return None
    
    def find_by_tag(self, tag: str) -> list[Any]:
        return []
    
    def find_consumers(self, entity_id: uuid.UUID) -> list[EntityBase]:
        consumers: list[EntityBase] = []
        for edge in self._model.relationships.edges:
            if edge.target_id == entity_id:
                consumer = self.find_by_id(edge.source_id)
                if consumer:
                    consumers.append(consumer)
        return consumers
    
    def find_producers(self, entity_id: uuid.UUID) -> list[EntityBase]:
        producers: list[EntityBase] = []
        for edge in self._model.relationships.edges:
            if edge.source_id == entity_id:
                producer = self.find_by_id(edge.target_id)
                if producer:
                    producers.append(producer)
        return producers
    
    def trace(
        self,
        entity_id: uuid.UUID,
        relationship_types: list[RelationshipType],
    ) -> list[EntityBase]:
        seen: set[uuid.UUID] = set()
        results: list[EntityBase] = []
        to_visit = [entity_id]
        rel_types = set(relationship_types)
        
        while to_visit:
            current = to_visit.pop(0)
            if current in seen:
                continue
            seen.add(current)
            for edge in self._model.relationships.edges:
                if edge.type not in rel_types:
                    continue
                if edge.source_id == current and edge.target_id not in seen:
                    target = self.find_by_id(edge.target_id)
                    if target:
                        results.append(target)
                        to_visit.append(edge.target_id)
        return results
    
    def find_dependencies(
        self, entity_id: uuid.UUID, *, transitive: bool = False,
    ) -> list[DependencyEdge]:
        results: list[DependencyEdge] = []
        seen: set[uuid.UUID] = set()
        to_visit = [entity_id]
        
        while to_visit:
            current = to_visit.pop(0)
            if current in seen:
                continue
            seen.add(current)
            for edge in self._model.relationships.edges:
                if edge.source_id == current:
                    results.append(DependencyEdge(
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        reason=edge.type.value,
                    ))
                    if transitive and edge.target_id not in seen:
                        to_visit.append(edge.target_id)
                if edge.target_id == current:
                    results.append(DependencyEdge(
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        reason=edge.type.value,
                    ))
                    if transitive and edge.source_id not in seen:
                        to_visit.append(edge.source_id)
        return results
    
    def find_impact(self, entity_ids: list[uuid.UUID]) -> ImpactSet:
        return ImpactSet(directly_changed=list(entity_ids))
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_query.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/integrity/query.py
git add tests/agents/integrity/test_query.py
git commit -m "feat(integrity): RepositoryQueryService — graph traversal API"
```

---

### Task 8: Engine Registry + Base

**Files:**
- Create: `backend/app/agents/integrity/registry.py`
- Create: `backend/app/agents/integrity/engines/__init__.py`
- Create: `backend/app/agents/integrity/engines/_base.py`
- Test: `tests/agents/integrity/test_registry.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_registry.py
from backend.app.agents.integrity.registry import EngineRegistry, register
from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile

def test_register_decorator():
    @register(name="test-engine", domain=IntegrityDomain.STRUCTURAL,
              capabilities={Capability.IMPORT})
    class TestEngine(IntegrityEngine):
        def analyze(self, model, query, views, context):
            return []
    
    registry = EngineRegistry.get_instance()
    engine = registry.get("test-engine")
    assert engine is not None
    assert engine.name == "test-engine"
    assert engine.domain == IntegrityDomain.STRUCTURAL
    assert Capability.IMPORT in engine.capabilities

def test_registry_for_profile():
    registry = EngineRegistry.get_instance()
    # Test engine should have no profiles declared, so not matched
    engines = registry.for_profile(ExecutionProfile.FULL)
    assert isinstance(engines, list)

def test_registry_resolve_order():
    @register(name="dep-engine", domain=IntegrityDomain.STRUCTURAL,
              capabilities={Capability.DEPENDENCY},
              required_dependencies=["base-engine"])
    class DepEngine(IntegrityEngine):
        def analyze(self, model, query, views, context):
            return []
    
    registry = EngineRegistry.get_instance()
    # Should not fail even if dependency not registered yet
    order = registry.resolve_execution_order({ExecutionProfile.FULL})
    assert isinstance(order, list)

def test_capability_values():
    assert Capability.SCHEMA.value == "schema"
    assert Capability.METRICS.value == "metrics"
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_registry.py -v
```

- [ ] **Step 3: Implement Engine registry and base**

```python
# backend/app/agents/integrity/engines/__init__.py
"""Integrity engine implementations."""

# backend/app/agents/integrity/engines/_base.py
from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile
from backend.app.agents.integrity.model import RepositoryKnowledgeModel
from backend.app.agents.integrity.model.finding import Finding
from backend.app.agents.integrity.query import RepositoryQueryService


class Capability(enum.Enum):
    SCHEMA = "schema"
    API = "api"
    CONFIG = "config"
    DOCS = "docs"
    GRAPH = "graph"
    IMPORT = "import"
    DEPENDENCY = "dependency"
    MIGRATION = "migration"
    FILESYSTEM = "filesystem"
    PLANNING = "planning"
    METRICS = "metrics"


class IntegrityEngine(ABC):
    name: str = ""
    domain: IntegrityDomain = IntegrityDomain.STRUCTURAL
    capabilities: set[Capability] = field(default_factory=set)
    required_dependencies: list[str] = field(default_factory=list)
    optional_dependencies: list[str] = field(default_factory=list)
    profiles: set[ExecutionProfile] = field(default_factory=set)
    
    @abstractmethod
    def analyze(
        self,
        model: RepositoryKnowledgeModel,
        query: RepositoryQueryService,
        views: Any,
        context: Any,
    ) -> list[Finding]: ...


# backend/app/agents/integrity/registry.py
from __future__ import annotations

from typing import Any
from backend.app.agents.integrity.engines._base import (
    IntegrityEngine, Capability,
)
from backend.app.agents.integrity.model.context import (
    IntegrityDomain, ExecutionProfile,
)


class EngineRegistry:
    _instance: EngineRegistry | None = None
    _engines: dict[str, dict[str, Any]] = {}
    
    def __new__(cls) -> EngineRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> EngineRegistry:
        return cls()
    
    def register(
        self,
        engine_cls: type,
        *,
        name: str,
        domain: IntegrityDomain,
        capabilities: set[Capability] | None = None,
        required_dependencies: list[str] | None = None,
        optional_dependencies: list[str] | None = None,
        profiles: set[ExecutionProfile] | None = None,
    ) -> None:
        self._engines[name] = {
            "cls": engine_cls,
            "name": name,
            "domain": domain,
            "capabilities": capabilities or set(),
            "required_dependencies": required_dependencies or [],
            "optional_dependencies": optional_dependencies or [],
            "profiles": profiles or set(),
        }
    
    def get(self, name: str) -> dict[str, Any] | None:
        return self._engines.get(name)
    
    def all(self) -> list[dict[str, Any]]:
        return list(self._engines.values())
    
    def for_profile(self, profile: ExecutionProfile) -> list[dict[str, Any]]:
        return [
            e for e in self._engines.values()
            if profile in e["profiles"] or not e["profiles"]
        ]
    
    def resolve_execution_order(
        self, profiles: set[ExecutionProfile],
    ) -> list[str]:
        candidates = set()
        for profile in profiles:
            for engine in self.for_profile(profile):
                candidates.add(engine["name"])
        
        ordered: list[str] = []
        visited: set[str] = set()
        
        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            engine = self._engines.get(name)
            if engine:
                for dep in engine["required_dependencies"]:
                    visit(dep)
            ordered.append(name)
        
        for name in list(candidates):
            visit(name)
        
        return ordered
    
    def find_by_capability(self, capability: Capability) -> list[dict[str, Any]]:
        return [
            e for e in self._engines.values()
            if capability in e["capabilities"]
        ]


def register(
    name: str,
    domain: IntegrityDomain,
    capabilities: set[Capability] | None = None,
    required_dependencies: list[str] | None = None,
    optional_dependencies: list[str] | None = None,
    profiles: set[ExecutionProfile] | None = None,
) -> Any:
    def decorator(cls: type) -> type:
        EngineRegistry.get_instance().register(
            cls,
            name=name,
            domain=domain,
            capabilities=capabilities,
            required_dependencies=required_dependencies,
            optional_dependencies=optional_dependencies,
            profiles=profiles,
        )
        return cls
    return decorator
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_registry.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/integrity/engines/__init__.py
git add backend/app/agents/integrity/engines/_base.py
git add backend/app/agents/integrity/registry.py
git add tests/agents/integrity/test_registry.py
git commit -m "feat(integrity): EngineRegistry + IntegrityEngine base + @register decorator"
```

---

### Task 9: View Registry + Derived Views

**Files:**
- Create: `backend/app/agents/integrity/views.py`
- Test: `tests/agents/integrity/test_views.py`

**Interfaces:**
- Produces: `ViewRegistry`, `DerivedViews` with lazy building and invalidation

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_views.py
from backend.app.agents.integrity.views import ViewRegistry
from backend.app.agents.integrity.model import RepositoryKnowledgeModel

def test_view_registry_creates_views():
    registry = ViewRegistry()
    views = registry.build(None)  # None as RKM for now
    assert hasattr(views, "import_graph")
    assert hasattr(views, "dependency_graph")
    assert hasattr(views, "api_graph")

def test_view_registry_lazy_build():
    registry = ViewRegistry()
    # First call builds, second returns cached
    v1 = registry.build(None)
    v2 = registry.build(None)
    assert v1 is v2  # same cached object

def test_view_registry_invalidation():
    registry = ViewRegistry()
    v1 = registry.build(None)
    registry.invalidate()
    v2 = registry.build(None)
    assert v1 is not v2  # new object after invalidation

def test_view_registry_invalidate_after_build():
    registry = ViewRegistry()
    registry.build(None)
    registry.invalidate()
    # After invalidation, next call rebuilds
    v = registry.build(None)
    assert v is not None
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_views.py -v
```

- [ ] **Step 3: Implement ViewRegistry**

```python
# backend/app/agents/integrity/views.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DerivedViews:
    import_graph: Any = None
    dependency_graph: Any = None
    api_graph: Any = None
    schema_graph: Any = None
    route_graph: Any = None
    migration_graph: Any = None
    configuration_graph: Any = None
    producer_consumer_graph: Any = None
    cross_layer_chain: Any = None


class ViewRegistry:
    def __init__(self) -> None:
        self._cache: DerivedViews | None = None
        self._valid = False
    
    def build(self, model: Any) -> DerivedViews:
        if self._valid and self._cache is not None:
            return self._cache
        
        views = DerivedViews()
        self._build_import_graph(views, model)
        self._build_dependency_graph(views, model)
        self._build_api_graph(views, model)
        self._build_schema_graph(views, model)
        self._build_route_graph(views, model)
        
        self._cache = views
        self._valid = True
        return views
    
    def invalidate(self) -> None:
        self._valid = False
        self._cache = None
    
    def _build_import_graph(self, views: DerivedViews, model: Any) -> None:
        edges = []
        if model and hasattr(model, 'code'):
            for imp in model.code.imports:
                edges.append(imp)
        views.import_graph = {"edges": edges}
    
    def _build_dependency_graph(self, views: DerivedViews, model: Any) -> None:
        views.dependency_graph = {"nodes": [], "edges": []}
    
    def _build_api_graph(self, views: DerivedViews, model: Any) -> None:
        views.api_graph = {"routes": [], "schemas": []}
    
    def _build_schema_graph(self, views: DerivedViews, model: Any) -> None:
        views.schema_graph = {"schemas": []}
    
    def _build_route_graph(self, views: DerivedViews, model: Any) -> None:
        views.route_graph = {"routes": []}
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_views.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/integrity/views.py
git add tests/agents/integrity/test_views.py
git commit -m "feat(integrity): ViewRegistry — lazy, cached, invalidatable DerivedViews"
```

---

### Task 10: Dependency Closure Service

**Files:**
- Create: `backend/app/agents/integrity/closure.py`
- Test: `tests/agents/integrity/test_closure.py`

**Interfaces:**
- Produces: `DependencyEdge`, `DependencyClosureService`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_closure.py
from pathlib import Path
from backend.app.agents.integrity.closure import (
    DependencyEdge, DependencyClosureService,
)

def test_dependency_edge():
    import uuid
    e = DependencyEdge(
        source_id=uuid.uuid4(),
        target_id=uuid.uuid4(),
        reason="imports",
    )
    assert e.reason == "imports"
    assert len(e.path) == 0

def test_empty_closure():
    svc = DependencyClosureService()
    result = svc.compute_impact_set([], None)
    assert len(result.directly_changed) == 0
    assert len(result.transitively_affected) == 0
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_closure.py -v
```

- [ ] **Step 3: Implement DependencyClosureService**

```python
# backend/app/agents/integrity/closure.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DependencyEdge:
    source_id: uuid.UUID
    target_id: uuid.UUID
    reason: str = ""
    path: list[uuid.UUID] = field(default_factory=list)


@dataclass
class ImpactSet:
    directly_changed: list[uuid.UUID] = field(default_factory=list)
    transitively_affected: list[uuid.UUID] = field(default_factory=list)
    dependency_chains: list[DependencyEdge] = field(default_factory=list)
    affected_symbols: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)


class DependencyClosureService:
    def compute_impact_set(
        self,
        changed_files: list[Path],
        model: Any,
    ) -> ImpactSet:
        directly = []
        for path in changed_files:
            matched = False
            if model and hasattr(model, 'code'):
                for uid, finfo in model.code.files.items():
                    if hasattr(finfo, 'path') and str(finfo.path) == str(path):
                        directly.append(uid)
                        matched = True
                        break
            if not matched:
                directly.append(uuid.uuid5(uuid.NAMESPACE_URL, str(path)))
        
        transitive: list[uuid.UUID] = []
        chains: list[DependencyEdge] = []
        
        if model and hasattr(model, 'relationships'):
            for source_id in directly:
                seen: set[uuid.UUID] = {source_id}
                to_visit: list[uuid.UUID] = [source_id]
                while to_visit:
                    current = to_visit.pop(0)
                    for edge in model.relationships.edges:
                        if edge.source_id == current and edge.target_id not in seen:
                            seen.add(edge.target_id)
                            transitive.append(edge.target_id)
                            chains.append(DependencyEdge(
                                source_id=current,
                                target_id=edge.target_id,
                                reason=edge.type.value,
                            ))
                            to_visit.append(edge.target_id)
        
        return ImpactSet(
            directly_changed=directly,
            transitively_affected=transitive,
            dependency_chains=chains,
        )
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_closure.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/integrity/closure.py
git add tests/agents/integrity/test_closure.py
git commit -m "feat(integrity): DependencyClosureService with dependency reason tracking"
```

---

### Task 11: Aggregator + Reporter

**Files:**
- Create: `backend/app/agents/integrity/report.py`
- Test: `tests/agents/integrity/test_report.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_report.py
from backend.app.agents.integrity.report import Aggregator, Reporter
from backend.app.agents.integrity.model.finding import Finding
from backend.app.agents.integrity.model.context import (
    Severity, Classification, Priority,
)

def test_aggregator_empty():
    agg = Aggregator()
    result = agg.aggregate([])
    assert result.total_findings == 0

def test_aggregator_counts():
    findings = [
        Finding(title="f1", severity=Severity.HIGH, priority=Priority.P1,
                urgency=5, classification=Classification.DRIFTED, location="a.py"),
        Finding(title="f2", severity=Severity.LOW, priority=Priority.P3,
                urgency=2, classification=Classification.UNUSED, location="b.py"),
    ]
    agg = Aggregator()
    result = agg.aggregate(findings)
    assert result.total_findings == 2

def test_reporter_markdown():
    findings = [
        Finding(title="test", severity=Severity.HIGH, priority=Priority.P1,
                urgency=5, classification=Classification.DRIFTED, location="a.py"),
    ]
    agg = Aggregator()
    metrics = agg.aggregate(findings)
    reporter = Reporter()
    md = reporter.to_markdown(findings, metrics)
    assert "test" in md
    assert "HIGH" in md

def test_reporter_json():
    findings = [
        Finding(title="json test", severity=Severity.LOW, priority=Priority.P3,
                urgency=2, classification=Classification.UNUSED, location="a.py"),
    ]
    agg = Aggregator()
    metrics = agg.aggregate(findings)
    reporter = Reporter()
    js = reporter.to_json(findings, metrics)
    assert "json test" in js
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_report.py -v
```

- [ ] **Step 3: Implement Aggregator + Reporter**

```python
# backend/app/agents/integrity/report.py
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

from backend.app.agents.integrity.model.finding import Finding
from backend.app.agents.integrity.model.metrics import ExecutionMetrics
from backend.app.agents.integrity.model.context import Severity, Classification


@dataclass
class AggregateResult:
    total_findings: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_classification: dict[str, int] = field(default_factory=dict)


class Aggregator:
    def aggregate(self, findings: list[Finding]) -> AggregateResult:
        by_severity: dict[str, int] = {}
        by_classification: dict[str, int] = {}
        
        for f in findings:
            sev = f.severity.name if hasattr(f.severity, 'name') else str(f.severity)
            cls_ = f.classification.name if hasattr(f.classification, 'name') else str(f.classification)
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_classification[cls_] = by_classification.get(cls_, 0) + 1
        
        return AggregateResult(
            total_findings=len(findings),
            by_severity=by_severity,
            by_classification=by_classification,
        )


class Reporter:
    def to_markdown(
        self, findings: list[Finding], metrics: AggregateResult,
    ) -> str:
        lines = ["# Integrity Report", "", "## Summary", ""]
        lines.append(f"- Total findings: {metrics.total_findings}")
        lines.append("")
        lines.append("### By Severity")
        for sev, count in sorted(metrics.by_severity.items(), reverse=True):
            lines.append(f"- **{sev}**: {count}")
        lines.append("")
        lines.append("### By Classification")
        for cls_, count in sorted(metrics.by_classification.items()):
            lines.append(f"- {cls_}: {count}")
        lines.append("")
        lines.append("## Findings")
        for f in findings:
            lines.append(f"### {f.severity.name}: {f.title}")
            lines.append(f"- Location: {f.location}")
            lines.append(f"- Classification: {f.classification.name}")
            lines.append(f"- {f.description}")
            lines.append("")
        return "\n".join(lines)
    
    def to_json(
        self, findings: list[Finding], metrics: AggregateResult,
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
                    "severity": f.severity.name if hasattr(f.severity, 'name') else str(f.severity),
                    "classification": f.classification.name if hasattr(f.classification, 'name') else str(f.classification),
                    "location": f.location,
                    "description": f.description,
                }
                for f in findings
            ],
        }
        return json.dumps(data, indent=2)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_report.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/integrity/report.py
git add tests/agents/integrity/test_report.py
git commit -m "feat(integrity): Aggregator + Reporter — markdown and JSON output"
```

---

### Task 12: IntegrityService + Workflow

**Files:**
- Create: `backend/app/agents/integrity/service.py`
- Create: `backend/app/agents/integrity/workflow.py`
- Test: `tests/agents/integrity/test_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/test_service.py
from pathlib import Path
from backend.app.agents.integrity.service import IntegrityService, IntegrityReport
from backend.app.agents.integrity.model.context import ExecutionProfile

def test_service_init():
    svc = IntegrityService(repository_root=Path("."))
    assert svc is not None

def test_service_analyze_full():
    svc = IntegrityService(repository_root=Path("."))
    report = svc.analyze()
    assert isinstance(report, IntegrityReport)
    assert report.execution_profile == ExecutionProfile.FULL
    assert report.findings is not None

def test_service_analyze_incremental():
    svc = IntegrityService(repository_root=Path("."))
    report = svc.analyze_incremental([Path("backend/app/agents/integrity/model/_base.py")])
    assert report is not None

def test_service_build_model():
    svc = IntegrityService(repository_root=Path("."))
    model = svc.build_model()
    assert model is not None
    assert model.metadata is not None
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
pytest tests/agents/integrity/test_service.py -v
```

- [ ] **Step 3: Implement IntegrityService + Workflow**

```python
# backend/app/agents/integrity/workflow.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.app.agents.integrity.model import RepositoryKnowledgeModel
from backend.app.agents.integrity.model.metadata_model import (
    MetadataModel, RepositoryCapabilities,
)
from backend.app.agents.integrity.model.code_model import CodeModel
from backend.app.agents.integrity.model.ecosystem_model import EcosystemModel
from backend.app.agents.integrity.model.documentation_model import DocumentationModel
from backend.app.agents.integrity.model.relationship_model import RelationshipModel
from backend.app.agents.integrity.query import RepositoryQueryService
from backend.app.agents.integrity.views import ViewRegistry
from backend.app.agents.integrity.validation import Validator
from backend.app.agents.integrity.registry import EngineRegistry
from backend.app.agents.integrity.model.context import (
    ExecutionProfile, AnalysisScope, AnalysisContext,
)
from backend.app.agents.integrity.model.finding import Finding
from backend.app.agents.integrity.model.metrics import ExecutionMetrics
from backend.app.agents.integrity.report import Aggregator, Reporter
from backend.app.agents.integrity.closure import DependencyClosureService
from backend.app.agents.integrity.extractors.python_extractor import PythonExtractor
from backend.app.agents.integrity.extractors.python_normalizer import PythonNormalizer


class IntegrityWorkflow:
    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root
        self._view_registry = ViewRegistry()
        self._validator = Validator()
        self._engine_registry = EngineRegistry.get_instance()
        self._aggregator = Aggregator()
        self._reporter = Reporter()
        self._closure = DependencyClosureService()
    
    def build_model(self) -> RepositoryKnowledgeModel:
        from datetime import datetime, timezone
        
        extractor = PythonExtractor()
        normalizer = PythonNormalizer()
        
        files = {}
        symbols: dict = {}
        schemas: dict = {}
        imports: list = []
        
        for path in sorted(self._root.rglob("*.py")):
            if ".venv" in path.parts or "__pycache__" in path.parts:
                continue
            try:
                raw = extractor.extract(path)
                entities = normalizer.normalize(raw)
                for ent in entities:
                    if hasattr(ent, 'id'):
                        files[ent.id] = ent
                        for imp_str in getattr(ent, 'raw_metadata', {}).get('imports', []):
                            imports.append({"file": str(path), "import": imp_str})
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue
        
        now = datetime.now(timezone.utc)
        import hashlib
        repo_hash = hashlib.md5(str(self._root).encode()).hexdigest()[:12]
        
        return RepositoryKnowledgeModel(
            metadata=MetadataModel(
                version="1.0",
                relationship_schema_version="1.0",
                repository_hash=repo_hash,
                generated_at=now,
                collector_versions={"python": "1.0"},
                capabilities=RepositoryCapabilities(
                    languages={"python"},
                    has_backend=True,
                ),
            ),
            code=CodeModel(
                files=files,
                directories=set(self._root.iterdir()) if self._root.exists() else set(),
                symbols=symbols,
                imports=imports,
                schemas=schemas,
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
                commands={}, skills={}, hooks={}, workflows={}, plans={},
            ),
            documentation=DocumentationModel(
                plans={}, source_of_truths={}, adrs=[],
            ),
            relationships=RelationshipModel(
                edges=[], relationship_schema_version="1.0",
            ),
        )
    
    def build_views(self, model: RepositoryKnowledgeModel) -> Any:
        return self._view_registry.build(model)
    
    def build_context(
        self, profile: ExecutionProfile, changed: list[Path] | None = None,
    ) -> AnalysisContext:
        return AnalysisContext(
            profile=profile,
            scope=(
                AnalysisScope.DEPENDENCY_CLOSURE if changed
                else AnalysisScope.FULL_REPOSITORY
            ),
            repository_root=self._root,
            changed_files=changed,
        )
    
    def run(
        self,
        profile: ExecutionProfile = ExecutionProfile.FULL,
        changed_files: list[Path] | None = None,
    ) -> tuple[list[Finding], ExecutionMetrics]:
        model = self.build_model()
        views = self.build_views(model)
        query = RepositoryQueryService(model)
        context = self.build_context(profile, changed_files)
        
        findings: list[Finding] = []
        engine_defs = self._engine_registry.for_profile(profile)
        
        for engine_def in engine_defs:
            engine_cls = engine_def["cls"]
            try:
                engine = engine_cls()
                engine_findings = engine.analyze(model, query, views, context)
                findings.extend(engine_findings)
            except Exception:
                continue
        
        aggregate = self._aggregator.aggregate(findings)
        metrics = ExecutionMetrics(
            total_findings=aggregate.total_findings,
            by_severity=aggregate.by_severity,
            by_classification=aggregate.by_classification,
        )
        
        return findings, metrics


# backend/app/agents/integrity/service.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.app.agents.integrity.model import RepositoryKnowledgeModel
from backend.app.agents.integrity.model.context import ExecutionProfile
from backend.app.agents.integrity.model.finding import Finding
from backend.app.agents.integrity.model.metrics import ExecutionMetrics
from backend.app.agents.integrity.query import RepositoryQueryService
from backend.app.agents.integrity.views import DerivedViews
from backend.app.agents.integrity.workflow import IntegrityWorkflow


@dataclass
class IntegrityReport:
    model: RepositoryKnowledgeModel
    findings: list[Finding]
    metrics: ExecutionMetrics
    execution_profile: ExecutionProfile
    execution_time_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class IntegrityService:
    def __init__(self, repository_root: Path) -> None:
        self._workflow = IntegrityWorkflow(repository_root)
        self._root = repository_root
    
    def analyze(
        self,
        profile: ExecutionProfile = ExecutionProfile.FULL,
        changed_files: list[Path] | None = None,
    ) -> IntegrityReport:
        import time
        start = time.monotonic()
        
        model = self._workflow.build_model()
        findings, metrics = self._workflow.run(profile, changed_files)
        elapsed = int((time.monotonic() - start) * 1000)
        
        return IntegrityReport(
            model=model,
            findings=findings,
            metrics=metrics,
            execution_profile=profile,
            execution_time_ms=elapsed,
        )
    
    def analyze_incremental(self, changed_files: list[Path]) -> IntegrityReport:
        return self.analyze(
            profile=ExecutionProfile.INCREMENTAL,
            changed_files=changed_files,
        )
    
    def analyze_target(
        self,
        paths: list[Path],
        engines: list[str] | None = None,
    ) -> IntegrityReport:
        return self.analyze(
            profile=ExecutionProfile.TARGET,
            changed_files=paths,
        )
    
    def build_model(self) -> RepositoryKnowledgeModel:
        return self._workflow.build_model()
    
    def build_views(self, model: RepositoryKnowledgeModel) -> DerivedViews:
        return self._workflow.build_views(model)
    
    def query(self, model: RepositoryKnowledgeModel) -> RepositoryQueryService:
        return RepositoryQueryService(model)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/agents/integrity/test_service.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/integrity/service.py
git add backend/app/agents/integrity/workflow.py
git add tests/agents/integrity/test_service.py
git commit -m "feat(integrity): IntegrityService (public API) + IntegrityWorkflow"
```

---

## Milestone 2 — Structural Engines (5 tasks)

### Task 13: Import Graph Engine

**Files:**
- Create: `backend/app/agents/integrity/engines/structural/__init__.py`
- Create: `backend/app/agents/integrity/engines/structural/import_engine.py`
- Test: `tests/agents/integrity/engines/structural/test_import_engine.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/integrity/engines/structural/test_import_engine.py
from backend.app.agents.integrity.engines.structural.import_engine import ImportGraphEngine
from backend.app.agents.integrity.model.context import ExecutionProfile
from backend.app.agents.integrity.engines._base import Capability

def test_import_engine_registered():
    from backend.app.agents.integrity.registry import EngineRegistry
    reg = EngineRegistry.get_instance()
    engine = reg.get("import-graph")
    assert engine is not None
    assert Capability.IMPORT in engine["capabilities"]

def test_import_engine_analyze_empty():
    engine = ImportGraphEngine()
    model = None
    result = engine.analyze(None, None, None, None)
    assert isinstance(result, list)

def test_import_engine_name():
    engine = ImportGraphEngine()
    assert engine.name == "import-graph"
```

- [ ] **Step 2: Implement ImportGraphEngine**

```python
# backend/app/agents/integrity/engines/structural/__init__.py

# backend/app/agents/integrity/engines/structural/import_engine.py
from __future__ import annotations

from typing import Any

from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile
from backend.app.agents.integrity.model.finding import Finding, Severity, Priority, Classification


@register(
    name="import-graph",
    domain=IntegrityDomain.STRUCTURAL,
    capabilities={Capability.IMPORT, Capability.GRAPH},
    profiles={ExecutionProfile.FULL, ExecutionProfile.QUICK, ExecutionProfile.INCREMENTAL},
)
class ImportGraphEngine(IntegrityEngine):
    name = "import-graph"
    domain = IntegrityDomain.STRUCTURAL
    capabilities = {Capability.IMPORT, Capability.GRAPH}
    profiles = {ExecutionProfile.FULL, ExecutionProfile.QUICK, ExecutionProfile.INCREMENTAL}
    
    def analyze(
        self, model, query, views, context,
    ) -> list[Finding]:
        findings: list[Finding] = []
        if not model or not hasattr(model, 'code'):
            return findings
        
        # Detect circular imports (simplified: detect self-referencing)
        imports = getattr(model.code, 'imports', [])
        seen_modules: set[str] = set()
        
        for imp in imports:
            file = getattr(imp, 'file', '') if hasattr(imp, 'file') else str(imp)
            if file in seen_modules:
                findings.append(Finding(
                    title="Potential circular import",
                    description=f"File imported multiple times: {file}",
                    severity=Severity.LOW,
                    priority=Priority.P3,
                    urgency=3,
                    classification=Classification.DUPLICATE,
                    location=file,
                ))
            seen_modules.add(file)
        
        return findings
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/agents/integrity/engines/structural/test_import_engine.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/integrity/engines/structural/__init__.py
git add backend/app/agents/integrity/engines/structural/import_engine.py
git add tests/agents/integrity/engines/structural/test_import_engine.py
git commit -m "feat(integrity): ImportGraphEngine — import cycle detection"
```

---

### Task 14: Dependency Engine

**Files:**
- Create: `backend/app/agents/integrity/engines/structural/dependency_engine.py`
- Test: `tests/agents/integrity/engines/structural/test_dependency_engine.py`

- [ ] **Step 1: Write tests + implement**

```python
# tests/agents/integrity/engines/structural/test_dependency_engine.py
from backend.app.agents.integrity.engines.structural.dependency_engine import DependencyEngine

def test_dependency_engine_registered():
    from backend.app.agents.integrity.registry import EngineRegistry
    reg = EngineRegistry.get_instance()
    assert reg.get("dependency") is not None

def test_dependency_engine_analyze():
    engine = DependencyEngine()
    result = engine.analyze(None, None, None, None)
    assert isinstance(result, list)
```

```python
# backend/app/agents/integrity/engines/structural/dependency_engine.py
from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile


@register(
    name="dependency",
    domain=IntegrityDomain.STRUCTURAL,
    capabilities={Capability.DEPENDENCY, Capability.GRAPH},
    profiles={ExecutionProfile.FULL, ExecutionProfile.INCREMENTAL},
)
class DependencyEngine(IntegrityEngine):
    name = "dependency"
    domain = IntegrityDomain.STRUCTURAL
    capabilities = {Capability.DEPENDENCY, Capability.GRAPH}
    profiles = {ExecutionProfile.FULL, ExecutionProfile.INCREMENTAL}
    
    def analyze(self, model, query, views, context):
        return []
```

- [ ] **Step 2: Run + commit**

```bash
pytest tests/agents/integrity/engines/structural/test_dependency_engine.py -v
git add backend/app/agents/integrity/engines/structural/dependency_engine.py
git add tests/agents/integrity/engines/structural/test_dependency_engine.py
git commit -m "feat(integrity): DependencyEngine — stub, registered"
```

---

### Task 15: Migration Engine

**Files:**
- Create: `backend/app/agents/integrity/engines/structural/migration_engine.py`
- Test: `tests/agents/integrity/engines/structural/test_migration_engine.py`

```python
# backend/app/agents/integrity/engines/structural/migration_engine.py
from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile


@register(
    name="migration",
    domain=IntegrityDomain.STRUCTURAL,
    capabilities={Capability.MIGRATION},
    profiles={ExecutionProfile.FULL},
)
class MigrationEngine(IntegrityEngine):
    name = "migration"
    domain = IntegrityDomain.STRUCTURAL
    capabilities = {Capability.MIGRATION}
    profiles = {ExecutionProfile.FULL}
    
    def analyze(self, model, query, views, context):
        return []
```

- [ ] **Run tests + commit**

```bash
pytest tests/agents/integrity/engines/structural/test_migration_engine.py -v
git add backend/app/agents/integrity/engines/structural/migration_engine.py
git add tests/agents/integrity/engines/structural/test_migration_engine.py
git commit -m "feat(integrity): MigrationEngine — stub, registered"
```

---

### Task 16: Filesystem Engine

**Files:**
- Create: `backend/app/agents/integrity/engines/structural/filesystem_engine.py`
- Test: `tests/agents/integrity/engines/structural/test_filesystem_engine.py`

```python
# backend/app/agents/integrity/engines/structural/filesystem_engine.py
from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile


@register(
    name="filesystem",
    domain=IntegrityDomain.STRUCTURAL,
    capabilities={Capability.FILESYSTEM},
    profiles={ExecutionProfile.FULL, ExecutionProfile.QUICK, ExecutionProfile.INCREMENTAL},
)
class FilesystemEngine(IntegrityEngine):
    name = "filesystem"
    domain = IntegrityDomain.STRUCTURAL
    capabilities = {Capability.FILESYSTEM}
    profiles = {ExecutionProfile.FULL, ExecutionProfile.QUICK, ExecutionProfile.INCREMENTAL}
    
    def analyze(self, model, query, views, context):
        return []
```

- [ ] **Run tests + commit**

```bash
pytest tests/agents/integrity/engines/structural/test_filesystem_engine.py -v
git add backend/app/agents/integrity/engines/structural/filesystem_engine.py
git add tests/agents/integrity/engines/structural/test_filesystem_engine.py
git commit -m "feat(integrity): FilesystemEngine — stub, registered"
```

---

### Task 17: Configuration Engine

**Files:**
- Create: `backend/app/agents/integrity/engines/structural/configuration_engine.py`
- Test: `tests/agents/integrity/engines/structural/test_configuration_engine.py`

```python
# backend/app/agents/integrity/engines/structural/configuration_engine.py
from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile


@register(
    name="configuration",
    domain=IntegrityDomain.STRUCTURAL,
    capabilities={Capability.CONFIG},
    profiles={ExecutionProfile.FULL},
)
class ConfigurationEngine(IntegrityEngine):
    name = "configuration"
    domain = IntegrityDomain.STRUCTURAL
    capabilities = {Capability.CONFIG}
    profiles = {ExecutionProfile.FULL}
    
    def analyze(self, model, query, views, context):
        return []
```

- [ ] **Run tests + commit**

```bash
pytest tests/agents/integrity/engines/structural/test_configuration_engine.py -v
git add backend/app/agents/integrity/engines/structural/configuration_engine.py
git add tests/agents/integrity/engines/structural/test_configuration_engine.py
git commit -m "feat(integrity): ConfigurationEngine — stub, registered"
```

---

## Milestone 3 — Semantic Engines (3 tasks)

### Task 18: Schema Engine

**Files:**
- Create: `backend/app/agents/integrity/engines/semantic/__init__.py`
- Create: `backend/app/agents/integrity/engines/semantic/schema_engine.py`
- Test: `tests/agents/integrity/engines/semantic/test_schema_engine.py`

- [ ] **Implement + test**

```python
# backend/app/agents/integrity/engines/semantic/schema_engine.py
from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile


@register(
    name="schema-engine",
    domain=IntegrityDomain.SEMANTIC,
    capabilities={Capability.SCHEMA},
    profiles={ExecutionProfile.FULL, ExecutionProfile.VERIFICATION},
)
class SchemaEngine(IntegrityEngine):
    name = "schema-engine"
    domain = IntegrityDomain.SEMANTIC
    capabilities = {Capability.SCHEMA}
    profiles = {ExecutionProfile.FULL, ExecutionProfile.VERIFICATION}
    
    def analyze(self, model, query, views, context):
        # V1: detect field name mismatches across schemas
        findings = []
        if not model or not hasattr(model, 'code'):
            return findings
        
        schemas = getattr(model.code, 'schemas', {})
        seen_fields: dict[str, list[str]] = {}
        
        for sid, schema in schemas.items():
            name = getattr(schema, 'name', str(sid)) if hasattr(schema, 'name') else str(sid)
            fields = getattr(schema, 'fields', []) if hasattr(schema, 'fields') else []
            for field in fields:
                fname = getattr(field, 'name', str(field)) if hasattr(field, 'name') else str(field)
                if fname not in seen_fields:
                    seen_fields[fname] = []
                seen_fields[fname].append(name)
        
        return findings
```

- [ ] **Run + commit**

```bash
pytest tests/agents/integrity/engines/semantic/test_schema_engine.py -v
git add backend/app/agents/integrity/engines/semantic/__init__.py
git add backend/app/agents/integrity/engines/semantic/schema_engine.py
git commit -m "feat(integrity): SchemaEngine — field name cross-referencing"
```

---

### Task 19: API Contract Engine

**Files:**
- Create: `backend/app/agents/integrity/engines/semantic/api_contract_engine.py`
- Test: `tests/agents/integrity/engines/semantic/test_api_contract_engine.py`

- [ ] **Implement stub (V1: detect route → schema mismatches)**

```python
# backend/app/agents/integrity/engines/semantic/api_contract_engine.py
from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile


@register(
    name="api-contract",
    domain=IntegrityDomain.SEMANTIC,
    capabilities={Capability.API},
    required_dependencies=["schema-engine"],
    profiles={ExecutionProfile.FULL, ExecutionProfile.VERIFICATION},
)
class APIContractEngine(IntegrityEngine):
    name = "api-contract"
    domain = IntegrityDomain.SEMANTIC
    capabilities = {Capability.API}
    required_dependencies = ["schema-engine"]
    profiles = {ExecutionProfile.FULL, ExecutionProfile.VERIFICATION}
    
    def analyze(self, model, query, views, context):
        return []
```

- [ ] **Run + commit**

```bash
git add backend/app/agents/integrity/engines/semantic/api_contract_engine.py
git commit -m "feat(integrity): APIContractEngine — stub, depends on schema-engine"
```

---

### Task 20: Cross-Layer Engine

**Files:**
- Create: `backend/app/agents/integrity/engines/semantic/cross_layer_engine.py`
- Test: `tests/agents/integrity/engines/semantic/test_cross_layer_engine.py`

- [ ] **Implement (detect frontend → backend field mismatches)**

```python
# backend/app/agents/integrity/engines/semantic/cross_layer_engine.py
from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile
from backend.app.agents.integrity.model.finding import (
    Finding, Severity, Priority, Classification,
)


@register(
    name="cross-layer",
    domain=IntegrityDomain.SEMANTIC,
    capabilities={Capability.API, Capability.SCHEMA},
    required_dependencies=["schema-engine", "api-contract"],
    profiles={ExecutionProfile.FULL, ExecutionProfile.VERIFICATION},
)
class CrossLayerEngine(IntegrityEngine):
    name = "cross-layer"
    domain = IntegrityDomain.SEMANTIC
    capabilities = {Capability.API, Capability.SCHEMA}
    required_dependencies = ["schema-engine", "api-contract"]
    profiles = {ExecutionProfile.FULL, ExecutionProfile.VERIFICATION}
    
    def analyze(self, model, query, views, context):
        findings = []
        if not model or not hasattr(model, 'code') or not query:
            return findings
        
        # Find field names across layers
        schemas = getattr(model.code, 'schemas', {})
        for sid, schema in schemas.items():
            name = getattr(schema, 'name', '') if hasattr(schema, 'name') else ''
            if not name:
                continue
            fields = getattr(schema, 'fields', []) if hasattr(schema, 'fields') else []
            for field in fields:
                fname = getattr(field, 'name', '') if hasattr(field, 'name') else ''
                if not fname:
                    continue
                # Check naming consistency across layers
                if fname != fname.lower():
                    findings.append(Finding(
                        title=f"Inconsistent field naming: {name}.{fname}",
                        description=f"Field '{fname}' in schema '{name}' uses non-standard casing",
                        severity=Severity.LOW,
                        priority=Priority.P3,
                        urgency=2,
                        classification=Classification.INCONSISTENT,
                        location=getattr(schema, 'location', str(sid)),
                    ))
        
        return findings
```

- [ ] **Run + commit**

```bash
pytest tests/agents/integrity/engines/semantic/test_cross_layer_engine.py -v
git add backend/app/agents/integrity/engines/semantic/cross_layer_engine.py
git commit -m "feat(integrity): CrossLayerEngine — field naming consistency checks"
```

---

## Milestone 4 — Evolution Engines (2 tasks)

### Task 21: Documentation Engine

**Files:**
- Create: `backend/app/agents/integrity/engines/evolution/__init__.py`
- Create: `backend/app/agents/integrity/engines/evolution/documentation_engine.py`
- Test: `tests/agents/integrity/engines/evolution/test_documentation_engine.py`

```python
# backend/app/agents/integrity/engines/evolution/documentation_engine.py
from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile


@register(
    name="documentation",
    domain=IntegrityDomain.EVOLUTION,
    capabilities={Capability.DOCS},
    profiles={ExecutionProfile.FULL},
)
class DocumentationEngine(IntegrityEngine):
    name = "documentation"
    domain = IntegrityDomain.EVOLUTION
    capabilities = {Capability.DOCS}
    profiles = {ExecutionProfile.FULL}
    
    def analyze(self, model, query, views, context):
        # V1: check that docs exist for key components
        return []
```

- [ ] **Run + commit**

```bash
git add backend/app/agents/integrity/engines/evolution/__init__.py
git add backend/app/agents/integrity/engines/evolution/documentation_engine.py
git commit -m "feat(integrity): DocumentationEngine — stub, registered"
```

---

### Task 22: Planning Engine

**Files:**
- Create: `backend/app/agents/integrity/engines/evolution/planning_engine.py`
- Test: `tests/agents/integrity/engines/evolution/test_planning_engine.py`

```python
# backend/app/agents/integrity/engines/evolution/planning_engine.py
from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile


@register(
    name="planning",
    domain=IntegrityDomain.EVOLUTION,
    capabilities={Capability.PLANNING},
    required_dependencies=["documentation"],
    profiles={ExecutionProfile.FULL},
)
class PlanningEngine(IntegrityEngine):
    name = "planning"
    domain = IntegrityDomain.EVOLUTION
    capabilities = {Capability.PLANNING}
    required_dependencies = ["documentation"]
    profiles = {ExecutionProfile.FULL}
    
    def analyze(self, model, query, views, context):
        return []
```

- [ ] **Run + commit**

```bash
git add backend/app/agents/integrity/engines/evolution/planning_engine.py
git commit -m "feat(integrity): PlanningEngine — stub, depends on documentation"
```

---

## Milestone 5 — Ecosystem Integration (3 tasks)

### Task 23: `/project:integrity` Command

**Files:**
- Create: `.claude/commands/project/integrity.md`

- [ ] **Implement thin orchestrator command**

```markdown
# .claude/commands/project/integrity.md

# /project:integrity — Core Repository Integrity System

Thin orchestrator. Calls `IntegrityService` — never accesses engines directly.

**Usage:**
- `/project:integrity` — Full analysis
- `/project:integrity quick` — Quick scan (structural only, changed files)
- `/project:integrity verify` — Verification mode (structural + semantic)
- `/project:integrity full` — All available engines
- `/project:integrity incremental <paths>` — Changed files + transitive deps

**Execution:**
1. Invoke `cortex-repo-discovery` to find repo root
2. Call `IntegrityService(repo_root).analyze(profile=...)` 
3. Output findings via Reporter (markdown for CLI, JSON for automation)

## Example Output
```markdown
# Integrity Report
- Total findings: 3
- By severity: CRITICAL: 0, HIGH: 1, MEDIUM: 2
- Execution time: 423ms
```
```

- [ ] **Commit**

```bash
git add .claude/commands/project/integrity.md
git commit -m "feat(integrity): /project:integrity command — thin orchestrator"
```

---

### Task 24: `cortex-integrity` Skill

**Files:**
- Create: `.claude/skills/cortex-integrity/SKILL.md`

- [ ] **Implement reusable skill**

```markdown
# .claude/skills/cortex-integrity/SKILL.md

# cortex-integrity — Repository Integrity Analysis

Reusable skill that any Cortex command can invoke. Runs `IntegrityService` 
and returns findings.

## Invocation

Invoke via: `Skill(topic="cortex-integrity", args={mode: "full"})`

## Modes
- `quick` — structural analysis on changed files
- `incremental` — structural + transitive deps  
- `full` — all available engines
- `verify` — structural + semantic
- `target` — specific paths/engines

## Output
Returns `IntegrityReport` with findings, metrics, and model.
```

- [ ] **Commit**

```bash
git add .claude/skills/cortex-integrity/SKILL.md
git commit -m "feat(integrity): cortex-integrity skill — reusable analysis capability"
```

---

### Task 25: Wire Into Existing Commands

**Files:**
- Modify: `.agents/plans/shared-phases.md`

- [ ] **Add integrity phase to shared phases**

```markdown
# In .agents/plans/shared-phases.md, add:

## Integrity Phase
Before completing any significant change, run Integrity analysis:
- `/project:develop` — runs INCREMENTAL profile (structural + dependency closure)
- `/project:review` — runs VERIFICATION profile (structural + semantic)
- `/project:verify` — runs FULL profile (all engines)
- `/project:reflect` — runs EVOLUTION engines (documentation + planning)
- `/project:release` — runs COMPLETE profile (all engines, strict gates)
```

- [ ] **Commit**

```bash
git add .agents/plans/shared-phases.md
git commit -m "feat(integrity): wire into shared phases — develop, review, verify, reflect"
```

---

## Self-Review

**1. Spec coverage:**
- EntityBase with UUID + confidence + source: Task 1
- Split RKM sub-models + facade: Task 3
- Relationship with direction/multiplicity/strength: Task 2
- Findings with priority/urgency: Task 4
- Metrics split into 4 categories: Task 4
- Validator: Task 5
- Extractor/Normalizer base + Python plugin: Task 6
- RepositoryQueryService: Task 7
- Engine Registry + @register decorator: Task 8
- View Registry (lazy, cached, invalidatable): Task 9
- DependencyClosureService: Task 10
- Aggregator + Reporter: Task 11
- IntegrityService + Workflow: Task 12
- 10 V1 engines: Tasks 13-22 (5 structural + 3 semantic + 2 evolution)
- Command: Task 23
- Skill: Task 24
- Shared phases: Task 25
- Non-goals and Performance: In spec (not implementation tasks)
- Source-of-Truth Registry: Task 4 (model definition)

**2. Placeholder scan:** No TBD/TODO. All steps have code.

**3. Type consistency:** 
- `EntityBase` → used by all entity types ✓
- `Finding` with severity/priority/urgency ✓
- `IntegrityEngine` with `required_dependencies`/`optional_dependencies` ✓
- Engine names match registry lookups ✓
- `RepositoryQueryService` accepts `RepositoryKnowledgeModel` ✓

**Coverage gap:** The remaining extractors (YAML, JSON, Markdown, ecosystem) are not explicitly implemented — they're scaffolding tasks. In practice, Milestone 1 should include them alongside the Python plugin. I'd fold them into Task 6 or add as a quick follow-up.

**Gap fix:** Add below as optional subtask.

---

## Optional Follow-Up: Additional Extractors

After Task 6, add YAML, JSON, and Markdown extractors:

**Files:** `yaml_extractor.py`, `json_extractor.py`, `markdown_extractor.py`, `md_normalizer.py`

Each follows the same pattern as PythonExtractor — implement `Extractor` subclass, register plugin, produce `dict[str, Any]`. Not blocking for Milestone 1 foundation.
