"""MCP tool wrapping — translate between MCP and Cortex tool formats.

MCP tools come in standard JSON-RPC format.
Cortex tools use OpenAI function-calling format.
This module bridges the two.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MCPToolWrapper:
    """Wrap an MCP tool for use in the Cortex agent loop.

    Handles:
    - Parameter translation (MCP inputSchema -> Cortex parameters)
    - Result translation (MCP result -> Cortex result)
    - Error handling (MCP errors -> Cortex errors)
    - Namespacing (mcp_{server}_{tool} to avoid collisions)
    """

    def __init__(self, server_name: str, mcp_tool: dict):
        self.server_name = server_name
        self.mcp_tool = mcp_tool
        self.tool_name = f"mcp_{server_name}_{mcp_tool.get('name', 'unknown')}"
        self.original_name = mcp_tool.get("name", "")

    def to_cortex_schema(self) -> dict:
        """Convert MCP tool to OpenAI function-calling format."""
        input_schema = self.mcp_tool.get("inputSchema", {})

        return {
            "type": "function",
            "function": {
                "name": self.tool_name,
                "description": self._translate_description(),
                "parameters": self._translate_parameters(input_schema),
            },
        }

    def _translate_description(self) -> str:
        """Add MCP server context to description."""
        original_desc = self.mcp_tool.get("description", "")
        return f"[MCP:{self.server_name}] {original_desc}"

    def _translate_parameters(self, input_schema: dict) -> dict:
        """Translate MCP inputSchema to OpenAI parameters format."""
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        translated_properties = {}
        for name, prop in properties.items():
            translated_properties[name] = {
                "type": prop.get("type", "string"),
                "description": prop.get("description", ""),
            }
            if "enum" in prop:
                translated_properties[name]["enum"] = prop["enum"]
            if "default" in prop:
                translated_properties[name]["default"] = prop["default"]

        return {
            "type": "object",
            "properties": translated_properties,
            "required": required,
        }

    async def execute(self, args: dict, transport: Any) -> Any:
        """Execute the MCP tool via the appropriate transport.

        Args:
            args: Tool arguments in Cortex format
            transport: MCP transport (stdio or SSE)

        Returns:
            Tool result in Cortex format
        """
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": self.original_name,
                "arguments": args,
            },
        }

        try:
            response = await transport.send_request(request)
            return self._translate_result(response)
        except Exception as e:
            logger.error("MCP tool %s execution failed: %s", self.tool_name, e)
            return {"error": str(e)}

    def _translate_result(self, mcp_result: dict) -> Any:
        """Translate MCP result to Cortex format."""
        content = mcp_result.get("result", {}).get("content", [])
        if not content:
            return mcp_result.get("result", {})

        texts = []
        for item in content:
            if item.get("type") == "text":
                texts.append(item.get("text", ""))

        if len(texts) == 1:
            try:
                return json.loads(texts[0])
            except json.JSONDecodeError:
                return {"text": texts[0]}
        elif texts:
            return {"text": "\n".join(texts)}
        else:
            return {"content": content}
