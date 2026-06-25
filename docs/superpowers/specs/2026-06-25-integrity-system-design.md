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
Integrity Workflow (phases, resolution, caching)
        │
Extractors (raw AST, JSON, YAML, filesystem metadata)
        │
Normalizers (convert to normalized entities)
        │
Repository Knowledge Model (versioned, immutable, with relationships)
        │
Dependency Closure Service (changed files → impact set)
        │
View Registry (lazy, cached — build on demand per mode)
        │
┌──────────────┬───────────────┬──────────────┐
│ Structural   │ Semantic      │ Evolution    │
│ Engines      │ Engines       │ Engines      │
└──────────────┴───────────────┴──────────────┘
        │              │                │
        └──────────────┼────────────────┘
                       ▼
              Findings Report
    (findings → recommendations → candidate fixes → metrics)
```

---

## Core Data Model

### Repository Knowledge Model

Immutable, versioned, in-memory semantic model of the repository. Built once per run. All engines read, none write.

```python
@dataclass(frozen=True)
class RepositoryKnowledgeModel:
    # Versioning
    version: str                         # RKM schema version
    repository_hash: str                 # hash of all collected files
    git_commit: str | None
    generated_at: datetime
    collector_versions: dict[str, str]
    
    # Filesystem
    files: dict[Path, FileInfo]
    directories: set[Path]
    
    # Code entities
    symbols: dict[str, list[SymbolDef]]
    imports: list[ImportEdge]
    schemas: dict[str, SchemaDef]
    types: dict[str, TypeDef]
    routes: list[RouteDef]
    routers: list[RouterDef]
    middleware: list[MiddlewareDef]
    models: dict[str, ORMModelDef]
    migrations: list[MigrationDef]
    db_config: DbConfigDef
    components: list[ComponentDef]
    api_clients: list[APIClientDef]
    configs: dict[str, ConfigDef]
    
    # Ecosystem
    commands: list[CommandDef]
    skills: list[SkillDef]
    hooks: list[HookDef]
    workflows: list[WorkflowDef]
    plans: list[PlanDef]
    
    # Explicit typed relationships
    relationships: list[Relationship]
```

### Findings

```python
@dataclass
class Recommendation:
    description: str
    priority: Priority

@dataclass
class CandidateFix:
    fix_type: FixType          # MANUAL | SCRIPT | PATCH
    fix_code: str | None
    autofix_available: bool
    estimated_effort: str
    breaking_change: bool

@dataclass
class Finding:
    id: str
    title: str
    description: str
    severity: Severity         # CRITICAL | HIGH | MEDIUM | LOW | INSIGHT
    classification: Classification  # MISSING | INCOMPATIBLE | AMBIGUOUS | UNUSED |
                                     # DUPLICATE | CIRCULAR | OBSOLETE | UNREACHABLE |
                                     # INCONSISTENT | DRIFTED
    location: str
    affected_components: list[str]
    dependency_chain: list[str]
    root_cause: str
    downstream_impact: str
    recommendation: Recommendation
    fix: CandidateFix | None
    confidence: float
    related_findings: list[str]
    owner: str | None
    tags: list[str]
    references: list[str]
```

### Metrics

```python
@dataclass
class IntegrityMetrics:
    integrity_score: float     # 0-100
    structural_score: float
    semantic_score: float
    evolution_score: float
    total_findings: int
    by_severity: dict[Severity, int]
    by_classification: dict[Classification, int]
    by_engine: dict[str, int]
    coverage: float
    confidence_distribution: list[float]
    execution_time_ms: int
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

## Plugin-Based Collectors

Extractors and Normalizers are separate concerns:

```
Filesystem
    │
    ├── Language Plugins
    │   ├── PythonExtractor    → PythonNormalizer
    │   ├── TypeScriptExtractor → TypeScriptNormalizer
    │   ├── YAMLExtractor      → YAMLNormalizer
    │   ├── JSONExtractor      → JSONNormalizer
    │   ├── MarkdownExtractor  → MarkdownNormalizer
    │
    ├── Framework Plugins
    │   ├── FastAPIExtractor   → FastAPINormalizer
    │   ├── ReactExtractor     → ReactNormalizer
    │   ├── SQLAlchemyExtractor→ SQLAlchemyNormalizer
    │
    └── Ecosystem Plugins
        ├── CommandExtractor   → CommandNormalizer
        ├── SkillExtractor     → SkillNormalizer
        ├── HookExtractor      → HookNormalizer
        └── WorkflowExtractor  → WorkflowNormalizer
```

---

## Derived Views

Lazy-built from the RKM on demand. Each is a graph structure reused across engines.

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

## Engine Interface

```python
class IntegrityEngine:
    name: str
    domain: IntegrityDomain          # STRUCTURAL | SEMANTIC | EVOLUTION
    profiles: set[ExecutionProfile]  # which profiles include this engine
    dependencies: list[str]          # other engines that must run first
    
    def analyze(
        self,
        model: RepositoryKnowledgeModel,
        views: DerivedViews,
        context: AnalysisContext,
    ) -> list[Finding]: ...
```

Engines register via decorator. Registry resolves topological execution order.

---

## Execution Profiles and Command Integration

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

## Implementation Milestones

### Milestone 1 — Foundation
- Repository Knowledge Model
- Collectors (Python + YAML + JSON + Markdown)
- Normalizers
- Derived Views (Import, Dependency, API, Cross-Layer)
- Dependency Closure Service
- Engine Registry
- Metrics
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
    workflow.py                # Integrity workflow orchestrator
    model.py                   # RKM + Finding + Relationship dataclasses
    context.py                 # AnalysisContext
    views.py                   # View registry + lazy builders
    closure.py                 # DependencyClosureService
    metrics.py                 # IntegrityMetrics
    registry.py                # EngineRegistry + @register decorator
    
    engines/
        __init__.py
        _base.py               # IntegrityEngine protocol + Finding sub-types
        
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
    
    extractors/
        __init__.py            # plugin registry
        _base.py               # Extractor + Normalizer protocols
        
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

.claude/commands/project/integrity.md
.claude/skills/cortex-integrity/SKILL.md
.agents/plans/shared-phases.md          # updated with integrity phase
```

---

## Deferred to V2

- Incremental cache layer (previous RKM → changed files → patch)
- Remaining 11 engines (P-C, Serialization, Type, State Flow, Middleware, Lifecycle, Route, Command, Skill, Repository Metrics, remaining Evolution)
- Auto-fix pipeline
- Persistent RKM storage
- Web dashboard for integrity metrics over time

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
