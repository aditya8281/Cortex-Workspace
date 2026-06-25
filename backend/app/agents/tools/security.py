"""Tool security — SSRF protection, path traversal prevention, command blocking.

Consolidates and extends security measures from the legacy tools.py.
"""

from __future__ import annotations

import ipaddress
import os
from pathlib import Path
from urllib.parse import urlparse

# Blocked command patterns — match lowercase version
BLOCKED_COMMANDS: list[str] = [
    # System destruction
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=",
    # Fork bomb
    ":(){ :|:& };:",
    # Permission changes
    "chmod 777",
    "chmod 4755",
    "chown",
    "passwd",
    # Power management
    "shutdown",
    "reboot",
    "halt",
    "init 0",
    "poweroff",
    "systemctl",
    "service",
    # Process killing
    "kill -9 1",
    "killall",
    # Package managers
    "apt ",
    "apt-get",
    "yum ",
    "dnf ",
    "pacman",
    "pip install",
    "pip3 install",
    "python -m pip install",
    "python3 -m pip install",
    "npm install",
    "npm i",
    # Network fetches (SSRF bypass via exec)
    "curl ",
    "curl -",
    "wget ",
    # Eval / exec
    "eval ",
    "exec ",
    # Cryptominers and known bad
    "minerd",
    "xmrig",
    "cryptonight",
]

# URL schemes blocked from web_fetch
BLOCKED_URL_SCHEMES = ("javascript:", "data:", "file:", "ftp:")

# Known private/reserved hostnames
BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "169.254.169.254",
        "metadata.google.internal",
        "metadata.google.internal.",
    }
)


def is_private_url(url: str) -> bool:
    """Check if URL targets a private/internal network (SSRF protection)."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        # Check known blocked hostnames
        if hostname in BLOCKED_HOSTNAMES:
            return True
        # Check private IP ranges
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
        except ValueError:
            # Not an IP — check DNS suffix
            if hostname.endswith(".internal") or hostname.endswith(".local") or hostname.endswith(".localhost"):
                return True
        return False
    except Exception:
        return False


def has_blocked_command(command: str) -> str | None:
    """Check if a command contains blocked patterns.

    Returns the matched pattern or None if safe.
    """
    cmd_lower = command.lower().strip()
    for pattern in BLOCKED_COMMANDS:
        if pattern in cmd_lower:
            return pattern
    return None


def ensure_within_workspace(file_path: str, workspace_root: str | None = None) -> Path:
    """Resolve and validate that a file path is within the agent workspace.

    Raises ValueError on path traversal.
    """
    root = workspace_root or os.environ.get(
        "AGENT_WORKSPACE",
        os.path.join(os.path.expanduser("~"), ".cortex-agent-workspace"),
    )
    workspace = Path(root).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    target = (workspace / file_path).resolve()
    if not str(target).startswith(str(workspace)):
        raise ValueError(f"Path traversal denied: {file_path}")
    return target
