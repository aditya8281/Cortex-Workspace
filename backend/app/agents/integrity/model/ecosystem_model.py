"""Ecosystem model — commands, skills, hooks, workflows, plans."""

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
