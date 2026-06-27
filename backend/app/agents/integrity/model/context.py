from __future__ import annotations

import enum
from dataclasses import dataclass
from pathlib import Path


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
