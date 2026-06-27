"""MCP bridge — connect MCP tools into the Cortex agent tool registry.

This module translates MCP discovery output into Cortex Tool objects
and registers them in the ToolRegistry, making MCP tools callable
from the agent loop.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.app.agents.tools.registry import Tool, ToolRegistry
from backend.app.mcp.wrapper import MCPToolWrapper

logger = logging.getLogger(__name__)


def register_mcp_tools(
    registry: ToolRegistry,
    mcp_tools: list[dict],
    server_name: str,
    transport: Any = None,
) -> int:
    """Register MCP tools as Cortex Tool objects in the ToolRegistry.

    Args:
        registry: Cortex ToolRegistry to register tools into
        mcp_tools: Raw MCP tool list from MCPServerDiscovery.get_all_tools()
        server_name: MCP server name for namespacing
        transport: MCP transport for tool execution (stdio or SSE)

    Returns:
        Number of tools registered
    """
    count = 0
    for mcp_tool in mcp_tools:
        try:
            wrapper = MCPToolWrapper(server_name, mcp_tool)
            cortex_tool = wrapper.to_cortex_schema()

            def _make_handler(w: MCPToolWrapper, t: Any) -> Any:
                async def handler(**kwargs: Any) -> Any:
                    return await w.execute(kwargs, t)
                return handler

            handler = _make_handler(wrapper, transport)

            tool = Tool(
                name=wrapper.tool_name,
                description=wrapper._translate_description(),
                handler=handler,
                schema=cortex_tool,
                requires_approval=False,
                category="mcp",
            )
            registry.register(tool)
            count += 1
            logger.debug("Registered MCP tool: %s", wrapper.tool_name)
        except Exception as e:
            logger.error("Failed to register MCP tool %s: %s", mcp_tool, e)

    logger.info("Registered %d MCP tools for server %s", count, server_name)
    return count
