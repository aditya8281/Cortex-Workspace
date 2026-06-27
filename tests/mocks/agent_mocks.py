"""Mock utilities for agent system testing."""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock


class MockTool:
    """Mock tool for testing agent tool execution."""

    def __init__(self, name: str, result: Any = None, error: str | None = None):
        self.name = name
        self.result = result
        self.error = error
        self.call_count = 0
        self.call_args_list = []

    async def execute(self, **kwargs) -> dict:
        self.call_count += 1
        self.call_args_list.append(kwargs)
        if self.error:
            return {"error": self.error}
        return {"result": self.result}


class MockAgentLoop:
    """Mock agent execution loop for testing."""

    def __init__(self):
        self.steps = []
        self.current_step = 0
        self.tools = {}
        self.llm_responses = []

    def register_tool(self, tool: MockTool):
        self.tools[tool.name] = tool

    def add_llm_response(self, response: dict):
        self.llm_responses.append(response)

    async def execute_step(self) -> dict:
        if self.current_step >= len(self.llm_responses):
            return {"done": True}
        response = self.llm_responses[self.current_step]
        self.steps.append(response)
        self.current_step += 1
        return response


def create_agent_response(
    content: str = "",
    tool_calls: list[dict] | None = None,
    finish_reason: str = "stop",
) -> dict:
    """Create a mock agent LLM response."""
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {
        "choices": [{"message": message, "finish_reason": finish_reason}],
        "model": "test-agent-model",
    }


def create_tool_call(tool_name: str, arguments: dict | None = None) -> dict:
    """Create a mock tool call for agent response."""
    return {
        "id": f"call_{tool_name}_001",
        "type": "function",
        "function": {"name": tool_name, "arguments": json.dumps(arguments or {})},
    }


def create_tool_result(tool_call_id: str, content: str = "Tool executed successfully") -> dict:
    """Create a mock tool result message."""
    return {"role": "tool", "tool_call_id": tool_call_id, "content": content}
