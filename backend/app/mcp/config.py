"""MCP configuration management.

Three levels of configuration:
1. System-level: default MCP servers (in config file)
2. User-level: per-user MCP server preferences
3. Session-level: temporary tool allowlists
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MCPConfig:
    """MCP configuration."""

    servers: list = field(default_factory=list)
    tool_allowlist: dict = field(default_factory=dict)
    tool_denylist: dict = field(default_factory=dict)


class MCPConfigManager:
    """Manage MCP configuration at all levels."""

    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".cortex"
        self._system_config: MCPConfig | None = None
        self._user_configs: dict[int, MCPConfig] = {}

    def load_system_config(self) -> MCPConfig:
        """Load system-level MCP configuration."""
        config_file = self.config_dir / "mcp_servers.yaml"
        if not config_file.exists():
            logger.info("No MCP config file found at %s", config_file)
            return MCPConfig()

        try:
            import yaml
        except ImportError:
            logger.warning("PyYAML not installed, cannot load MCP config")
            return MCPConfig()

        with open(config_file) as f:
            data = yaml.safe_load(f) or {}

        from .discovery import MCPServerConfig

        servers = []
        for server_data in data.get("servers", []):
            servers.append(
                MCPServerConfig(
                    name=server_data["name"],
                    command=server_data.get("command", ""),
                    args=server_data.get("args", []),
                    env=server_data.get("env", {}),
                    transport=server_data.get("transport", "stdio"),
                    sse_url=server_data.get("sse_url"),
                    working_dir=server_data.get("working_dir"),
                )
            )

        self._system_config = MCPConfig(servers=servers)
        return self._system_config

    def get_user_tools(self, user_id: int, all_tools: list[dict]) -> list[dict]:
        """Filter tools based on user's allowlist/denylist."""
        user_config = self._user_configs.get(user_id, MCPConfig())
        allowlist = user_config.tool_allowlist.get(user_id, [])
        denylist = user_config.tool_denylist.get(user_id, [])

        if allowlist:
            return [t for t in all_tools if t["function"]["name"] in allowlist]
        elif denylist:
            return [t for t in all_tools if t["function"]["name"] not in denylist]
        return all_tools
