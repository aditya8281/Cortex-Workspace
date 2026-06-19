"""Base protocol for services that can be consumed via HTTP or Tauri IPC."""

from abc import ABC, abstractmethod
from typing import Any


class ServiceProtocol(ABC):
    """Base protocol for services that can be consumed via HTTP or Tauri IPC."""

    @abstractmethod
    async def execute(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a service action with given parameters."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is healthy."""
        ...
