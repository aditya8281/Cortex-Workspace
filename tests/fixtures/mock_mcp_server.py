#!/usr/bin/env python3
"""Mock MCP server for testing. Runs as subprocess for integration tests.

Protocol: JSON-RPC 2.0 over stdio (one JSON object per line).

Usage:
    python tests/fixtures/mock_mcp_server.py
"""

from __future__ import annotations

import json
import sys

SERVER_INFO = {
    "name": "mock-mcp-server",
    "version": "1.0.0",
}

TOOLS = [
    {
        "name": "mock_tool",
        "description": "A mock tool for testing",
        "inputSchema": {
            "type": "object",
            "properties": {"input": {"type": "string", "description": "Input text"}},
            "required": ["input"],
        },
    },
    {
        "name": "add_numbers",
        "description": "Add two numbers together",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
        },
    },
]


def handle_request(request: dict) -> dict:
    """Handle a JSON-RPC request and return a response."""
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "serverInfo": SERVER_INFO,
                "capabilities": {"tools": {}},
            },
        }
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS},
        }
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name == "mock_tool":
            text = f"Mock result: {arguments.get('input', '')}"
        elif tool_name == "add_numbers":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            text = str(a + b)
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": text}]},
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


def main():
    """Read JSON-RPC requests from stdin and write responses to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
