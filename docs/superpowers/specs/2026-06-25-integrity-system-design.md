# Cortex Core Repository Integrity System

**Version:** 1.0
**Status:** Draft
**Date:** 2026-06-25

---

## Overview

The Cortex Integrity System is a **general-purpose repository analysis framework** — not just a command. It provides a normalized, versioned, in-memory model of the entire repository (the **Repository Knowledge Model**), builds derived graph views from it, and runs modular **Integrity Engines** that produce findings, recommendations, and metrics.

Architected as a **platform service** — existing Cortex commands (`develop`, `review`, `verify`, `reflect`, `health`, `release`) become clients that request specific integrity modes.

---

## Architecture

```
/project:integrity (thin orchestrator)
        │
IntegrityService (stable public API — analyze / analyze_incremental / report)
        │
Integrity Workflow (phases, resolution, caching)
        │
Extractors (raw AST, JSON, YAML, filesystem metadata)
        │
Normalizers (convert to normalized entities)
        │
Validator (reject malformed entities before they enter the model)
        │
┌───────────────────────────────────────────────┐
│      Repository Knowledge Model (façade)      │
│  ┌───────────┐ ┌────────────┐ ┌────────────┐ │
│  │CodeModel  │ │EcosystemMdl│ │DocModel    │ │
│  ├───────────┤ ├────────────┤ ├────────────┤ │
│  │ symbols   │ │ commands   │ │ plans      │ │
│  │ schemas   │ │ skills     │ │ docs       │ │
│  │ routes    │ │ hooks      │ │ specs      │ │
│  │ models    │ │ workflows  │ │            │ │
│  │ imports   │ │ configs    │ │            │ │
│  │ types     │ └────────────┘ └────────────┘ │
│  └───────────┘                                │
│  ┌───────────┐ ┌────────────────────────────┐ │
│  │RelMdl     │ │MetadataModel               │ │
│  ├───────────┤ ├────────────────────────────┤ │
│  │relationshp│ │ version, repo_hash,        │ │
│  │edges      │ │ generated_at, capabilitie  │ │
│  └───────────┘ └────────────────────────────┘ │
└───────────────────────────────────────────────┘
        │
RepositoryQueryService (graph traversal — trace / find / impact)
        │
Dependency Closure Service (changed files → impact set + dependency reasons)
        │
View Registry (lazy, cached, invalidatable — build on demand per mode)
        │
┌──────────────┬───────────────┬──────────────┐
│ Structural   │ Semantic      │ Evolution    │
│ Engines      │ Engines       │ Engines      │
└──────────────┴───────────────┴──────────────┘
        │              │                │
        └──────────────┼────────────────┘
                       ▼
              Aggregator + Reporter
     (findings → aggregate → markdown/json/html/cli)
                       ▼
              Metrics (split: Integrity / Repository Analytics /
                      Performance / Execution)
```

---

## Core Data Model

### Repository Knowledge Model

Immutable, versioned, in-memory semantic model of the repository. Built once per run. All engines read, none write. Implemented as a **façade over bounded sub-models** to prevent god-object growth. (#1)

Every entity carries a stable UUID. All relationships reference IDs, not names. Each collected fact records its confidence and source collector.

```python
@dataclass(frozen=True)
class EntityBase:
    id: UUID                           # stable identifier — never changes
    confidence: float                   # 1.0 = exact, <1.0 = inferred
    source_collector: str              # which extractor produced this
    source_version: str                # collector version

@dataclass(frozen=True)
class MetadataModel:
    version: str                         # RKM schema version
    relationship_schema_version: str     # relationship type catalog version
    repository_hash: str                 # hash of all collected files
    git_commit: str | None
    generated_at: datetime
    collector_versions: dict[str, str]   # {collector_name: version}
    capabilities: RepositoryCapabilities  # languages/frameworks detected in repo (#6)

# Repository capabilities — engines auto-disable if their capability is absent
@dataclass(frozen=True)
class RepositoryCapabilities:
    languages: set[str]       # {"python", "typescript", "yaml", ...}
    frameworks: set[str]      # {"fastapi", "react", "sqlalchemy", ...}
    has_frontend: bool
    has_backend: bool
    has_database_migrations: bool
    has_docker: bool
    has_ci: bool

@dataclass(frozen=True)
class CodeModel:
    files: dict[UUID, FileInfo]
    directories: set[Path]
    symbols: dict[UUID, SymbolDef]
    imports: list[ImportEdge]
    schemas: dict[UUID, SchemaDef]
    types: dict[UUID, TypeDef]
    routes: dict[UUID, RouteDef]
    routers: dict[UUID, RouterDef]
    middleware: dict[UUID, MiddlewareDef]
    models: dict[UUID, ORMModelDef]
    migrations: dict[UUID, MigrationDef]
    db_config: DbConfigDef
    components: dict[UUID, ComponentDef]
    api_clients: dict[UUID, APIClientDef]
    configs: dict[UUID, ConfigDef]

@dataclass(frozen=True)
class EcosystemModel:
    commands: dict[UUID, CommandDef]
    skills: dict[UUID, SkillDef]
    hooks: dict[UUID, HookDef]
    workflows: dict[UUID, WorkflowDef]
    plans: dict[UUID, PlanDef]

@dataclass(frozen=True)
class DocumentationModel:
    plans: dict[UUID, PlanDef]         # same entities, bounded context view
    source_of_truths: dict[UUID, SourceOfTruth]
    adrs: list[ADREntry]

@dataclass(frozen=True)
class RelationshipModel:
    edges: list[Relationship]          # typed edges between entities
    relationship_schema_version: str

# ── Façade ────────────────────────────────────────
@dataclass(frozen=True)
class RepositoryKnowledgeModel:
    metadata: MetadataModel
    code: CodeModel
    ecosystem: EcosystemModel
    documentation: DocumentationModel
    relationships: RelationshipModel
```

Every entity type extends `EntityBase`:

```python
@dataclass(frozen=True)
class RouteDef(EntityBase):
    path: str
    methods: list[str]
    ...

@dataclass(frozen=True)
class SchemaDef(EntityBase):
    name: str
    fields: list[FieldDef]
    ...
```

### Relationships

First-class typed edges between entities. Most engines operate on relationships rather than raw entities. Every relationship carries direction semantics — not all dependencies are equal. (#5)

```python
class RelationshipDirection(Enum):
    DIRECTED   = "directed"    # one-way: A → B
    BIDIRECTIONAL = "bidirectional"  # A ↔ B
    TRANSITIVE = "transitive"  # A → B → C (derived)

class Multiplicity(Enum):
    ONE_TO_ONE     = "1:1"
    ONE_TO_MANY    = "1:N"
    MANY_TO_MANY   = "N:N"

class EdgeStrength(Enum):
    STRONG    = "strong"     # structural (import, extends)
    MEDIUM    = "medium"     # semantic (calls, produces)
    WEAK      = "weak"       # inferred (references, documents)

class RelationshipType(Enum):
    IMPORTS       = "imports"
    IMPLEMENTS    = "implements"
    CALLS         = "calls"
    RETURNS       = "returns"
    ACCEPTS       = "accepts"
    SERIALIZES    = "serializes"
    DESERIALIZES  = "deserializes"
    DEPENDS_ON    = "depends_on"
    PRODUCES      = "produces"
    CONSUMES      = "consumes"
    REFERENCES    = "references"
    DOCUMENTS     = "documents"
    EXTENDS       = "extends"
    MIGRATES_TO   = "migrates_to"
    CONFIGURES    = "configures"
    OWNS          = "owns"
    TESTS         = "tests"
    VALIDATES     = "validates"

@dataclass(frozen=True)
class Relationship:
    id: UUID
    type: RelationshipType
    direction: RelationshipDirection
    multiplicity: Multiplicity
    strength: EdgeStrength
    source_id: UUID                    # source entity UUID
    target_id: UUID                    # target entity UUID
    metadata: dict[str, str] | None    # e.g. {"line": "42", "file": "app.py"}
    confidence: float
    source_collector: str
```

Relationship schema versioning (`relationship_schema_version` on `MetadataModel`) tracks the RelationshipType catalog.

### Findings

```python
@dataclass
class Finding:
    id: str
    title: str
    description: str
    severity: Severity         # CRITICAL | HIGH | MEDIUM | LOW | INSIGHT
    priority: Priority         # P0 | P1 | P2 | P3 (urgency for ordering) (#11)
    urgency: int               # 1-10, independent of severity
    classification: Classification  # MISSING | INCOMPATIBLE | AMBIGUOUS | UNUSED |
                                     # DUPLICATE | CIRCULAR | OBSOLETE | UNREACHABLE |
                                     # INCONSISTENT | DRIFTED
    location: str
    affected_components: list[str]
    dependency_chain: list[str]
    root_cause: str
    downstream_impact: str
    recommendation: str        # human-readable suggested action
    fix: CandidateFix | None
    confidence: float
    related_findings: list[str]
    owner: str | None
    tags: list[str]
    references: list[str]
```

### Metrics (Four Categories)

Repository intelligence metrics split into four categories. V1 captures core Integrity scores and basic Execution metrics; Repository Analytics and Performance metrics expand in V2.

```python
# ── Integrity Scores (V1) ──────────────────────────
@dataclass
class IntegrityScores:
    integrity_score: float       # 0-100 — weighted composite
    structural_score: float
    semantic_score: float
    evolution_score: float

# ── Repository Analytics (V2+) ─────────────────────
@dataclass
class RepositoryAnalytics:
    dependency_density: float               # edges / nodes
    fan_in_distribution: dict[str, int]     # most-imported modules
    fan_out_distribution: dict[str, int]    # widest deps
    architectural_hotspots: list[str]       # high churn + high deps
    coupling_coefficient: float             # interconnectedness
    cycles: int                             # circular dependency count
    # V2 adds: ownership, documentation coverage, test coverage, instability

# ── Performance Metrics (V2+) ──────────────────────
@dataclass
class PerformanceMetrics:
    collection_time_ms: int
    view_build_time_ms: int
    analysis_time_ms: int
    peak_memory_mb: float

# ── Execution Metrics (V1) ─────────────────────────
@dataclass
class ExecutionMetrics:
    total_findings: int
    by_severity: dict[Severity, int]
    by_classification: dict[Classification, int]
    by_engine: dict[str, int]
    coverage: float              # % of repo entities inspected
    confidence_distribution: list[float]
```

### Analysis Context

```python
# Execution profiles — what engines run
class ExecutionProfile(Enum):
    QUICK        = "quick"         # structural only, changed files
    INCREMENTAL  = "incremental"   # structural + dep closure, changed files
    VERIFICATION = "verification"  # structural + semantic, affected components
    FULL         = "full"          # all domain engines, entire repo
    COMPLETE     = "complete"      # all engines, strict gates
    TARGET       = "target"        # specified engines, specified paths

# Analysis scope — breadth of repository traversal
class AnalysisScope(Enum):
    FILES_CHANGED       = "files_changed"
    DEPENDENCY_CLOSURE  = "dependency_closure"
    FULL_REPOSITORY     = "full_repository"

@dataclass
class AnalysisContext:
    profile: ExecutionProfile  # which engines to run
    scope: AnalysisScope       # how far to traverse
    changed_files: list[Path] | None
    target_paths: list[Path] | None
    target_engines: list[str] | None  # for TARGET profile
    repository_root: Path
    feature_name: str | None
    branch: str | None
    active_version: str | None
    active_phase: str | None
    execution_reason: str | None
```

---

## Validation Stage

Inserted between normalization and model construction to keep the RKM trustworthy. Malformed entities are rejected before they enter the model. (#3)

```python
class ValidationResult:
    passed: bool
    errors: list[ValidationError]
    warnings: list[str]

class Validator:
    def validate_entity(self, entity: EntityBase) -> ValidationResult:
        """Check required fields, type constraints, UUID consistency."""
    
    def validate_relationship(self, rel: Relationship) -> ValidationResult:
        """Verify source/target IDs exist, direction is valid."""
    
    def validate_model(self, model: RepositoryKnowledgeModel) -> ValidationResult:
        """Cross-entity consistency checks (e.g. all referenced UUIDs resolve)."""

# Pipeline: Extractor → Normalizer → Validator → RepositoryKnowledgeModel
```

V1 checks: required fields present, UUIDs non-null, confidence in [0,1], source references resolve. V2 adds cross-entity and cross-model consistency.

---

## Plugin-Based Collectors

Each plugin declares its compatibility — plugin version, supported RKM schema version, and supported language/framework version — enabling safe evolution. (#4)

```python
@dataclass
class CollectorPlugin:
    name: str
    plugin_version: str               # plugin itself versioned
    supported_rkm_version: str        # e.g. "1.x"
    supported_language_version: str | None  # e.g. "3.9+"

class Extractor(ABC):
    def __init__(self, plugin: CollectorPlugin): ...
    @abstractmethod
    def extract(self, path: Path) -> dict[str, Any]: ...

class Normalizer(ABC):
    def __init__(self, plugin: CollectorPlugin): ...
    @abstractmethod
    def normalize(self, raw: dict[str, Any]) -> list[EntityBase]: ...

# Plugin tree
# Filesystem
#     ├── Language Plugins
#     │   ├── PythonExtractor(version="1.0", rkm="1.x", lang="3.9+")
#     │   │   → PythonNormalizer
#     │   ├── TypeScriptExtractor → TypeScriptNormalizer
#     │   ├── YAMLExtractor → YAMLNormalizer
#     │   ├── JSONExtractor → JSONNormalizer
#     │   └── MarkdownExtractor → MarkdownNormalizer
#     ├── Framework Plugins
#     │   ├── FastAPIExtractor → FastAPINormalizer
#     │   ├── ReactExtractor → ReactNormalizer
#     │   └── SQLAlchemyExtractor → SQLAlchemyNormalizer
#     └── Ecosystem Plugins
#         ├── CommandExtractor → CommandNormalizer
#         ├── SkillExtractor → SkillNormalizer
#         ├── HookExtractor → HookNormalizer
#         └── WorkflowExtractor → WorkflowNormalizer
```

---

## Derived Views

Lazy-built from the RKM on demand and cached. Views support invalidation when the RKM is updated, enabling incremental scans without full rebuild. (#10)

Each view is a graph structure reused across engines.

| View | Source Entities | Purpose |
|------|----------------|---------|
| Import Graph | imports | Which files import which |
| Dependency Graph | imports + symbols | Transitive dependency chain |
| API Graph | routes + routers + schemas | Route → handler → schema |
| Schema Graph | schemas + types | Field lineage, hierarchy |
| Route Graph | routes | Route tree, prefix nesting |
| Migration Graph | migrations | Chain ordering, conflicts |
| Configuration Graph | configs | Inheritance, overrides |
| Producer-Consumer Graph | symbols + imports + routes | Who produces, who consumes |
| Cross-Layer Chain | components → api_clients → routes → models → migrations | Full front-to-back |

---

## IntegrityService (Public API)

The stable public interface that all Cortex commands interact with. This is the boundary between the Integrity platform and the rest of the ecosystem — commands never call engines, views, or the workflow directly. (#4)

```python
class IntegrityService:
    def __init__(self, repository_root: Path): ...
    
    def analyze(
        self,
        profile: ExecutionProfile = ExecutionProfile.FULL,
        changed_files: list[Path] | None = None,
    ) -> IntegrityReport:
        """Run integrity analysis. The primary entry point.
        
        Args:
            profile: Which execution profile to use.
            changed_files: For INCREMENTAL profile — only these and their
                          transitive dependencies are analyzed.
        Returns:
            IntegrityReport containing findings, metrics, and metadata.
        """
    
    def analyze_incremental(self, changed_files: list[Path]) -> IntegrityReport:
        """Convenience wrapper — runs INCREMENTAL profile."""
    
    def analyze_target(
        self,
        paths: list[Path],
        engines: list[str] | None = None,
    ) -> IntegrityReport:
        """Analyze only specific paths, optionally with specific engines."""
    
    def build_model(self) -> RepositoryKnowledgeModel:
        """Collect and normalize the repository into the RKM (cached per run)."""
    
    def build_views(self, model: RepositoryKnowledgeModel) -> DerivedViews:
        """Build derived graph views from the model."""
    
    def query(self, model: RepositoryKnowledgeModel) -> RepositoryQueryService:
        """Get a query service for the model."""
    
    def report(self, findings: list[Finding], metrics: ...) -> IntegrityReport:
        """Aggregate and format findings into a report."""

@dataclass
class IntegrityReport:
    model: RepositoryKnowledgeModel
    findings: list[Finding]
    metrics: IntegrityScores | ExecutionMetrics
    execution_profile: ExecutionProfile
    execution_time_ms: int
    metadata: dict[str, Any]
```

---

## Engine Interface

```python
class Capability(Enum):
    SCHEMA     = "schema"
    API        = "api"
    CONFIG     = "config"
    DOCS       = "docs"
    GRAPH      = "graph"
    IMPORT     = "import"
    DEPENDENCY = "dependency"
    MIGRATION  = "migration"
    FILESYSTEM = "filesystem"
    PLANNING   = "planning"
    METRICS    = "metrics"

class IntegrityEngine:
    name: str
    domain: IntegrityDomain                  # STRUCTURAL | SEMANTIC | EVOLUTION
    capabilities: set[Capability]            # what this engine knows about
    required_dependencies: list[str]         # engines that MUST run first (#9)
    optional_dependencies: list[str]         # degrades gracefully if absent
    
    def analyze(
        self,
        model: RepositoryKnowledgeModel,
        query: RepositoryQueryService,
        views: DerivedViews,
        context: AnalysisContext,
    ) -> list[Finding]: ...
```

Engines register via decorator. Registry resolves execution order by dependency graph and supports capability-based lookups (e.g. "find all engines with SCHEMA capability").

---

## RepositoryQueryService

A dedicated service for graph traversal over the RKM. Separated from the model to prevent mixing storage with querying — which enables future caching and optimizations without changing the model. (#2)

```python
class RepositoryQueryService:
    """Graph traversal over the Repository Knowledge Model.
    
    The primary interface between engines and the model. Engines should
    rarely access RKM sub-models directly.
    """
    
    def __init__(self, model: RepositoryKnowledgeModel): ...
    
    # ── Entity lookup ────────────────────────────────
    def find_routes(self, path_pattern: str | None = None) -> list[RouteDef]: ...
    def find_schemas(self, field_name: str) -> list[SchemaDef]: ...
    def find_by_id(self, entity_id: UUID) -> EntityBase | None: ...
    def find_by_tag(self, tag: str) -> list[EntityBase]: ...
    
    # ── Consumer / Producer ──────────────────────────
    def find_consumers(self, entity_id: UUID) -> list[EntityBase]:
        """Everything that references entity_id."""
    def find_producers(self, entity_id: UUID) -> list[EntityBase]:
        """Everything that entity_id references."""
    
    # ── Trace ────────────────────────────────────────
    def trace(
        self, entity_id: UUID,
        relationship_types: list[RelationshipType],
    ) -> list[EntityBase]:
        """Follow typed edges from entity."""
    
    def trace_api(self, route_id: UUID) -> list[EntityBase]:
        """Route → handler → schema → model chain."""
    
    def trace_schema(self, schema_id: UUID) -> list[EntityBase]:
        """Schema → field types → referenced schemas → serializers."""
    
    def trace_frontend(self, component_id: UUID) -> list[EntityBase]:
        """Component → API client → route → schema chain."""
    
    def trace_cross_layer(self, entity_id: UUID) -> list[list[EntityBase]]:
        """Full front-to-back chain: component → client → route → schema → model → migration."""
    
    # ── Dependency ───────────────────────────────────
    def find_dependencies(
        self, entity_id: UUID, *, transitive: bool = False,
    ) -> list[DependencyEdge]:
        """Import/dependency graph traversal."""
    
    def find_impact(self, entity_ids: list[UUID]) -> ImpactSet:
        """For changed entities, find all potentially affected."""
```

---

## Dependency Closure Service

```python
@dataclass
class DependencyEdge:
    source_id: UUID
    target_id: UUID
    reason: str                          # WHY: "imports", "extends", "calls" (#9)
    path: list[UUID]                     # transitive chain for traceability

class DependencyClosureService:
    def compute_impact_set(
        self,
        changed_files: list[Path],
        model: RepositoryKnowledgeModel,
    ) -> ImpactSet:
        """Compute transitive closure with dependency reasons.
        
        Returns:
            directly_changed: list[UUID]
            transitively_affected: list[UUID]
            dependency_chains: list[DependencyEdge]  # full WHY trace
            affected_symbols: list[str]
            affected_components: list[str]
        """
```

---

## Source-of-Truth Registry

A registry of canonical sources in the repository that Evolution engines reason against generically, rather than hardcoding each artifact type. (#13)

```python
@dataclass(frozen=True)
class SourceOfTruth:
    id: UUID
    name: str                              # e.g. "architecture", "plans", "docs"
    entity_type: str                       # PLANS | DOCS | ARCHITECTURE | COMMANDS | SKILLS | WORKFLOWS
    path: Path                             # location in repository
    schema_version: str | None             # version of the source format
    validation_rules: list[str]            # e.g. "every command must have a matching skill"
```

Evolution engines query the registry; they don't hardcode artifact locations.

---

## Event Bus (Architecture Note)

Deferred to V2. The workflow is designed so that a pub/sub layer can be inserted between engine outputs without changing engine interfaces:

```
Before (V1): Workflow → Engine A → Engine B  (sequential)
After  (V2): Workflow → Engine A → Event → Engine B subscribes
```

Engine outputs remain the same `list[Finding]` — only the orchestration changes.

---

| Command | Execution Profile | V1 Engines (10) | V2+ Engines (11) |
|---------|-------------------|-----------------|-------------------|
| `/project:develop` | INCREMENTAL | Import + Dependency + Filesystem + Configuration + DependencyClosure | P-C + Middleware + Lifecycle + Route |
| `/project:review` | VERIFICATION | Import + Dependency + Schema + API Contract + Cross-Layer | P-C + Serialization + Type + State Flow |
| `/project:verify` | FULL (Structural + Semantic) | All 5 Structural + all 3 Semantic | Remaining Structural + Semantic |
| `/project:reflect` | FULL (Evolution only) | Documentation + Planning | Architecture + Command + Skill + Workflow + Hook + Template + Governance + Version + ADR + Metrics |
| `/project:health` | FULL (Structural only) | Import + Dependency + Migration + Filesystem + Configuration | Route + Middleware + Lifecycle + Metrics |
| `/project:release` | COMPLETE | All 10 V1 engines | All V2 engines, strict gates |
| `/project:integrity` | Any (user selects) | Any combination | Any combination |

---

## V1 Scope: 10 Engines (Vertical Slice)

### Structural (5)
1. **Import Graph Engine** — cycle detection, dead imports, orphan modules
2. **Dependency Engine** — missing/stale dependencies
3. **Migration Engine** — chain gaps, ordering, merge conflicts
4. **Filesystem Engine** — expected-missing files, orphan artifacts
5. **Configuration Engine** — env drift, missing/unknown config keys

### Semantic (3)
6. **Schema Engine** — field type/name mismatches across layers
7. **API Contract Engine** — request/response mismatches, missing endpoints
8. **Cross-Layer Engine** — full front-to-back chain verification (component → client → route → schema → model → migration)

### Evolution (2)
9. **Documentation Engine** — docs vs implementation drift
10. **Planning Engine** — plans vs implementation drift

---

## Non-Goals

What Integrity explicitly does **not** do — preventing scope creep.

- Does **not** execute code. Static analysis only.
- Does **not** replace tests. Integrity finds *structural* mismatches, not logic bugs.
- Does **not** benchmark runtime. No performance profiling, no latency measurement.
- Does **not** lint style. Code formatting, naming conventions, and docstring coverage are out of scope.
- Does **not** perform security penetration testing. No injection detection, no secret scanning, no vuln assessment.
- Does **not** deploy changes. Analysis only; no auto-fix execution (V2 adds optional patches).
- Does **not** persist the RKM across runs. In-memory only (persistence is V2).

## Performance Characteristics

Expected computational complexity by analysis stage:

| Stage | Complexity | Notes |
|-------|-----------|-------|
| Collection | O(files) | Linear in repository file count |
| Normalization | O(entities) | One pass per extracted entity |
| Validation | O(entities) | One pass per normalized entity |
| Import Graph construction | O(edges) | Edges = import statements |
| Dependency Closure | O(V + E) | BFS/DFS over import graph |
| View construction | O(entities × relationships) | Per-view filters |
| Schema Graph | O(nodes) | Schema hierarchy traversal |
| Cross-Layer Trace | O(layers × edges) | Depth bounded by architecture depth |
| Engine execution | O(engine_count × graph_size) | Parallelizable per engine |

**Target:** Full-repository scan < 5 seconds for repos under 50k files. Incremental scans (< 20 changed files) complete in < 1 second.

---

## Implementation Milestones

### Milestone 1 — Foundation
- RKM sub-models: `MetadataModel`, `CodeModel`, `EcosystemModel`, `DocumentationModel`, `RelationshipModel`, `RepositoryCapabilities`
- RKM façade assembling sub-models
- Collectors (Python + YAML + JSON + Markdown) with plugin versioning
- Normalizers
- **Validator** — entity and relationship validation
- `RepositoryQueryService` — graph traversal API
- Derived Views (Import, Dependency, API, Cross-Layer) with invalidation
- Dependency Closure Service
- Engine Registry with capability-based lookup
- `IntegrityService` — stable public API
- Metrics (IntegrityScores + ExecutionMetrics)
- Aggregator + Reporter
- Integrity Workflow

**No real engines yet** — infrastructure only.

### Milestone 2 — Structural Engines
- Import Graph Engine
- Dependency Engine
- Migration Engine
- Filesystem Engine
- Configuration Engine

**End-to-end structural analysis operational.**

### Milestone 3 — Semantic Engines
- Schema Engine
- API Contract Engine
- Cross-Layer Engine

**Integrity proves cross-boundary value.**

### Milestone 4 — Evolution Engines
- Documentation Engine
- Planning Engine

**All 10 V1 engines operational.**

### Milestone 5 — Ecosystem Integration
- `/project:integrity` command (thin orchestrator)
- `cortex-integrity` skill (reusable intelligence)
- Wire into: `develop` (INCREMENTAL), `review` (VERIFICATION), `verify` (FULL), `reflect` (FULL — Evolution engines)
- Shared phases in `.agents/plans/shared-phases.md`

---

## Filesystem Layout

```
backend/app/agents/integrity/
    __init__.py
    service.py               # IntegrityService — stable public API (#4)
    workflow.py               # Integrity workflow orchestrator
    
    model/
        __init__.py           # RKM façade — assembles sub-models
        _base.py              # EntityBase, EntityType
        metadata_model.py     # MetadataModel, RepositoryCapabilities (#6)
        code_model.py         # CodeModel — files, symbols, routes, schemas, types, models
        ecosystem_model.py    # EcosystemModel — commands, skills, hooks, workflows
        documentation_model.py# DocumentationModel — plans, SoT registries, ADRs
        relationship_model.py # RelationshipModel — typed edges between entities
        finding.py            # Finding, Recommendation, CandidateFix
        metrics.py            # IntegrityScores, RepositoryAnalytics, ExecutionMetrics
        context.py            # AnalysisContext, ExecutionProfile, AnalysisScope
        source_of_truth.py    # SourceOfTruth registry (#13)
    
    query.py                  # RepositoryQueryService — graph traversal (#2)
    validation.py             # Validator — entity + relationship + model validation (#3)
    views.py                  # View registry + lazy builders (invalidatable) (#10)
    closure.py                # DependencyClosureService
    registry.py               # EngineRegistry + @register decorator
    
    report.py                 # Aggregator + Reporter — findings → markdown/json/html/cli (#8)
    
    engines/
        __init__.py
        _base.py              # IntegrityEngine protocol + Capability enum
        
        structural/
            import_engine.py
            dependency_engine.py
            migration_engine.py
            filesystem_engine.py
            configuration_engine.py
        
        semantic/
            schema_engine.py
            api_contract_engine.py
            cross_layer_engine.py
        
        evolution/
            documentation_engine.py
            planning_engine.py
    
    extractors/               # Plugin-based collectors (#1, #4)
        __init__.py           # CollectorsPlugin registry
        _base.py              # Extractor, Normalizer, CollectorPlugin protocols
        
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

.claude/commands/project/integrity.md     # thin orchestrator → calls IntegrityService
.claude/skills/cortex-integrity/SKILL.md  # reusable skill → calls IntegrityService
.agents/plans/shared-phases.md            # updated with integrity phase
```

---

## Deferred to V2

- Incremental cache layer (previous RKM → changed files → patch)
- Remaining 11 engines (P-C, Serialization, Type, State Flow, Middleware, Lifecycle, Route, Command, Skill, Repository Metrics, remaining Evolution)
- **Test Engine** — verify every public API, route, migration, command has tests (#12)
- **Test coverage awareness** — RKM tracks test↔implementation relationships
- Auto-fix pipeline + **Fix Provider plugin system** (#8)
- Event bus architecture — pub/sub between engine outputs (#5)
- Persistent RKM storage (SQLite-backed, incremental updates)
- **Knowledge Graph persistence** — RKM written to local store for reuse across sessions
- **Historical integrity** — track integrity scores over time, trend detection, regression alerts
- Web dashboard for integrity metrics over time
- **Analytics expansion** — ownership concentration, instability scores, documentation coverage (#10)
- **Split Cross-Layer Engine** into independent Frontend→API, API→Service, Service→ORM, ORM→Migration, Migration→DB engines (#14)
- **AI fix planning** — Finding → Planning Engine → Patch Proposal → Review → Apply
- **Engine composition** — engines call other engines through capabilities instead of directly

---

## Validation

- Unit tests per engine (mock RKM + expected findings)
- Integration tests (real repo scan, verify findings against known issues)
- Performance test: whole-repo scan < 5s for repos under 50k files
- Regression: each milestone keeps existing tests passing (base ~1000)
- Ecosystem: verify each command integration produces correct mode output

---

## References

- [Cortex Guide — .agents/plans/guide.md](/.agents/plans/guide.md)
- [Architecture Principles — docs/ARCHITECTURE.md](/docs/ARCHITECTURE.md)
- [V1 Phase Plan — .agents/plans/versions/v1/Phase-3.md](/.agents/plans/versions/v1/Phase-3.md)
- [Skill-First Architecture — CLAUDE.md](/CLAUDE.md)
