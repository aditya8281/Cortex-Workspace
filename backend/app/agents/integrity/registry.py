"""Engine registry — singleton registry, @register decorator, capability lookup."""

from __future__ import annotations

from typing import Any

from backend.app.agents.integrity.engines._base import IntegrityEngine, Capability
from backend.app.agents.integrity.model.context import IntegrityDomain, ExecutionProfile


class EngineRegistry:
    """Singleton registry for integrity engine implementations.

    Engines register themselves via the @register decorator at import time.
    """

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
            e
            for e in self._engines.values()
            if profile in e["profiles"] or not e["profiles"]
        ]

    def resolve_execution_order(self, profiles: set[ExecutionProfile]) -> list[str]:
        candidates: set[str] = set()
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
            e
            for e in self._engines.values()
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
    """Decorator that registers an engine class into the EngineRegistry."""
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
