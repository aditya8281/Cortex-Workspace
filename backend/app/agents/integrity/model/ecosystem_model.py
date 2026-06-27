"""Ecosystem model — commands, skills, hooks, workflows, plans."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EcosystemModel:
    commands: dict[uuid.UUID, Any]
    skills: dict[uuid.UUID, Any]
    hooks: dict[uuid.UUID, Any]
    workflows: dict[uuid.UUID, Any]
    plans: dict[uuid.UUID, Any]
