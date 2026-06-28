"""Environment scanner — returns safe, non-secret environment variables via strict allowlist."""

from __future__ import annotations

import os

# Strict allowlist of safe environment variables
SAFE_ENV_VARS: list[str] = [
    "HOME",
    "SHELL",
    "LANG",
    "PATH",
    "USER",
    "LOGNAME",
    "HOSTNAME",
    "TERM",
    "EDITOR",
    "VISUAL",
    "CORTEX_ROOT",
    "APP_NAME",
    "API_V1_PREFIX",
    "PYTHON_VERSION",
    "NODE_VERSION",
]

# Patterns that indicate secrets — never returned even if accidentally added to allowlist
SECRET_PATTERNS: list[str] = [
    "SECRET",
    "PASSWORD",
    "TOKEN",
    "API_KEY",
    "PRIVATE",
    "CREDENTIALS",
    "AUTH",
    "DATABASE_URL",
    "REDIS_URL",
]


class EnvironmentScannerService:
    """Safe environment variable scanner — strict allowlist approach."""

    def get_environment(self, user_id: int) -> dict[str, str]:  # noqa: ARG002
        """Get relevant (safe) environment variables.

        Returns only variables in the allowlist.
        Never returns secrets.
        """
        safe_vars: dict[str, str] = {}
        for var_name in SAFE_ENV_VARS:
            if _is_secret(var_name):
                continue
            value = os.environ.get(var_name)
            if value:
                safe_vars[var_name] = value
        return safe_vars

    def get_system_paths(self) -> dict[str, str]:
        """Get important system paths."""
        return {
            "home": os.path.expanduser("~"),
            "temp": os.path.join(os.path.expanduser("~"), "tmp"),
            "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
            "documents": os.path.join(os.path.expanduser("~"), "Documents"),
        }

    def get_safe_env_check(self) -> list[dict[str, str | bool]]:
        """Check which safe variables are set.

        Returns list of {name, is_set} for all safe variables.
        """
        return [{"name": var, "is_set": os.environ.get(var) is not None} for var in SAFE_ENV_VARS]


def _is_secret(name: str) -> bool:
    """Return True if *name* matches any secret pattern."""
    upper = name.upper()
    return any(pattern in upper for pattern in SECRET_PATTERNS)
