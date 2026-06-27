"""Tool domain mapping — P05 Task 3.

Maps tool names to Cortex domains for permission scoping and organization.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Domain definitions: domain_name -> {tools: set[str], read_only: set[str]}
TOOL_DOMAINS: dict[str, dict[str, set[str]]] = {
    "memory": {
        "tools": {"search_memory", "create_memory", "update_memory", "delete_memory", "list_memories"},
        "read_only": {"search_memory", "list_memories"},
    },
    "awareness": {
        "tools": {"read_file", "write_file", "list_files", "search_files", "file_info"},
        "read_only": {"read_file", "list_files", "search_files", "file_info"},
    },
    "cognition": {
        "tools": {"think", "analyze", "summarize", "compare"},
        "read_only": {"think", "analyze", "summarize", "compare"},
    },
    "web": {
        "tools": {"web_search", "web_fetch", "url_info"},
        "read_only": {"web_search", "web_fetch", "url_info"},
    },
    "communication": {
        "tools": {"send_email", "read_email", "list_emails", "send_notification"},
        "read_only": {"read_email", "list_emails"},
    },
    "system": {
        "tools": {"execute_command", "run_script", "system_info", "process_list"},
        "read_only": {"system_info", "process_list"},
    },
    "code": {
        "tools": {"edit_code", "run_tests", "lint_code", "format_code", "search_code"},
        "read_only": {"search_code", "lint_code"},
    },
}


@dataclass
class ToolDomainMap:
    """Maps tool names to domains for scoping and permissions."""

    _reverse_map: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Build reverse lookup: tool_name -> domain."""
        for domain, config in TOOL_DOMAINS.items():
            for tool in config["tools"]:
                self._reverse_map[tool] = domain

    def get_domain(self, tool_name: str) -> str:
        """Get the domain for a tool. Returns 'unknown' if not mapped."""
        return self._reverse_map.get(tool_name, "unknown")

    def is_read_only(self, tool_name: str) -> bool:
        """Check if a tool is read-only in its domain."""
        domain = self.get_domain(tool_name)
        if domain == "unknown":
            return False
        return tool_name in TOOL_DOMAINS[domain]["read_only"]

    def get_tools_for_domains(self, domains: list[str]) -> list[str]:
        """Get all tool names across the given domains."""
        tools: list[str] = []
        for domain in domains:
            config = TOOL_DOMAINS.get(domain)
            if config:
                tools.extend(sorted(config["tools"]))
        return tools

    def get_domain_summary(self) -> dict[str, dict[str, int]]:
        """Get a summary of each domain: tool count, read-only count."""
        summary: dict[str, dict[str, int]] = {}
        for domain, config in TOOL_DOMAINS.items():
            summary[domain] = {
                "tool_count": len(config["tools"]),
                "read_only_count": len(config["read_only"]),
            }
        return summary
