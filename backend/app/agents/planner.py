"""Planner agent — breaks tasks into structured subtask plans.

Deprecated: Will be replaced by the V1 Phase-2 streaming loop (loop.py).
Planning becomes a tool call within the loop, not a separate agent.
Kept as fallback until the new loop is feature-complete.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backend.app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are a planner agent for a code intelligence system.
Your job is to break down user tasks into a structured plan of subtasks.

For each subtask, specify:
1. "goal" — what needs to be accomplished
2. "agent" — which agent type should handle it: "executor", "researcher", or "reviewer"
3. "dependencies" — list of subtask indices that must complete first (0-indexed)
4. "expected_output" — what the subtask should produce

Output your plan as a JSON array. Example:
[
  {"goal": "Search for all auth-related code", "agent": "executor",
   "dependencies": [], "expected_output": "List of auth files"},
  {"goal": "Analyze auth flow for vulnerabilities",
   "agent": "researcher", "dependencies": [0],
   "expected_output": "Security analysis report"},
  {"goal": "Write a summary of findings",
   "agent": "executor", "dependencies": [1],
   "expected_output": "Markdown summary"}
]

If the task is simple enough to not need planning, return a single-step plan.
Always return valid JSON."""


class PlannerAgent(BaseAgent):
    """Plans tasks and delegates to specialized agents."""

    def __init__(self, llm_chat: Any | None = None):
        super().__init__(system_prompt=PLANNER_SYSTEM_PROMPT)
        self._llm_chat = llm_chat

    def _default_prompt(self) -> str:
        return PLANNER_SYSTEM_PROMPT

    async def run(self, input_text: str, _context: dict | None = None) -> str:
        """Plan a task — returns JSON plan string."""
        plan = await self.plan(input_text)
        return json.dumps(plan, indent=2)

    async def plan(self, task: str) -> list[dict]:
        """Create a structured plan for a task.

        If an LLM chat function is configured, uses it.
        Otherwise, returns a simple single-step plan.
        """
        if self._llm_chat:
            return await self._plan_with_llm(task)
        return self._plan_simple(task)

    async def _plan_with_llm(self, task: str) -> list[dict]:
        """Use LLM to generate a plan."""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": task},
            ]
            assert self._llm_chat is not None
            result = await self._llm_chat(messages)
            text = result[0] if isinstance(result, tuple) else str(result)
            return self._parse_plan(text)
        except Exception as e:
            logger.warning("LLM planning failed, using simple plan: %s", e)
            return self._plan_simple(task)

    def _plan_simple(self, task: str) -> list[dict]:
        """Create a simple single-step plan without LLM."""
        return [
            {
                "goal": task,
                "agent": "executor",
                "dependencies": [],
                "expected_output": "Task completion result",
            }
        ]

    def _parse_plan(self, text: str) -> list[dict]:
        """Parse LLM response into structured plan."""
        try:
            # Try to extract JSON from the response
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse plan JSON, using raw text")
            return [
                {
                    "goal": text.strip(),
                    "agent": "executor",
                    "dependencies": [],
                    "expected_output": "Result",
                }
            ]
