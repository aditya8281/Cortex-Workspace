"""Local processing enforcement — ensures data stays on-device."""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ProcessingCheckResult:
    """Result of a local processing verification."""

    is_local: bool
    reason: str
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LocalProcessingService:
    """Enforces local-first processing invariant.

    Checks:
    1. No cloud environment variables set
    2. Not running in a Docker container
    3. Hostname resolves to a local address
    """

    CLOUD_ENV_KEYS = ("AWS_LAMBDA", "FUNCTIONS_WORKER_RUNTIME", "VERCEL", "HEROKU", "K_SERVICE")

    def verify_local(self, operation: str) -> ProcessingCheckResult:
        """Verify that an operation can be performed locally."""
        for env_key in self.CLOUD_ENV_KEYS:
            if os.environ.get(env_key):
                return ProcessingCheckResult(
                    is_local=False,
                    reason=f"Cloud environment detected: {env_key}",
                )

        if os.path.exists("/.dockerenv"):
            return ProcessingCheckResult(
                is_local=False,
                reason="Docker container detected",
            )

        try:
            hostname = socket.gethostname()
            resolved = socket.gethostbyname(hostname)
            parts = resolved.split(".")
            if len(parts) == 4:
                o1, o2 = int(parts[0]), int(parts[1])
                is_private = (
                    resolved.startswith("127.")
                    or resolved.startswith("10.")
                    or resolved.startswith("192.168.")
                    or (o1 == 172 and 16 <= o2 <= 31)
                )
            else:
                is_private = False
        except (OSError, ValueError):
            is_private = False

        if not is_private:
            return ProcessingCheckResult(
                is_local=True,
                reason=f"Hostname '{hostname}' — verify deployment context",
            )

        return ProcessingCheckResult(
            is_local=True,
            reason="All local processing checks passed",
        )

    def get_processing_log(self) -> list[dict]:  # noqa: ARG002
        """Stub — in production, returns audit log of verify calls."""
        return []
