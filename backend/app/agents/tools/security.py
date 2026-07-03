"""Tool security — SSRF protection, path traversal prevention, command blocking.

Consolidates and extends security measures from the legacy tools.py.
"""

from __future__ import annotations

import ipaddress
import os
from pathlib import Path
from urllib.parse import urlparse

# Blocked command patterns — match lowercase version.
# Convention: patterns with trailing space block a command invocation (e.g. "apt " blocks "apt install"
# but not "aptitude"). Patterns without trailing space block the word as a substring, used for
# unique tokens unlikely in innocent commands (e.g. "mkfs", "pacman", "xmrig").
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
    "exec /",  # exec with absolute path
    "exec sh",  # exec shell
    "exec bash",  # exec bash
    "exec python",  # exec python
    "exec .",  # exec with relative path (./)
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

    Absolute paths are allowed if they fall within the user's home directory.
    Relative paths are resolved within the agent workspace.

    Raises ValueError on path traversal.
    """
    resolved = Path(file_path).expanduser().resolve()

    # ── Absolute path: check against workspace_root or home directory ──
    if file_path.startswith("/") or file_path.startswith("~"):
        root = workspace_root or os.environ.get("AGENT_WORKSPACE")
        if root:
            workspace = Path(root).resolve()
            try:
                resolved.relative_to(workspace)
                return resolved
            except ValueError:
                pass  # Check home directory below
        home = Path.home().resolve()
        try:
            resolved.relative_to(home)
        except ValueError:
            raise ValueError(f"Path traversal denied: {file_path}")
        return resolved

    # ── Relative path: resolve within agent workspace ──
    root = workspace_root or os.environ.get(
        "AGENT_WORKSPACE",
        os.environ.get("CORTEX_ROOT", None),
    )
    if not root:
        root = os.path.join(os.path.expanduser("~"), ".cortex-agent-workspace")
    workspace = Path(root).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    target = (workspace / file_path).resolve()
    try:
        target.relative_to(workspace)
    except ValueError:
        raise ValueError(f"Path traversal denied: {file_path}")
    return target
