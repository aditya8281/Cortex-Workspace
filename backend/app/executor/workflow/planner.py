from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from backend.app.executor.schemas import IntentDecision, IntentType
from backend.app.executor.workflow.models import WorkflowPlan, WorkflowStepPlan


_SEARCH_HINTS = (
    "find",
    "search",
    "locate",
    "where",
    "contains",
    "containing",
    "trace",
)

_READ_HINTS = (
    "explain",
    "summarize",
    "summary",
    "analyse",
    "analyze",
    "inspect",
    "understand",
    "review",
)

_MEMORY_HINTS = (
    "memory",
    "remember",
    "previous",
    "prior",
    "last time",
    "recent",
    "history",
)

_RAG_HINTS = (
    "architecture",
    "codebase",
    "implementation",
    "module",
    "class",
    "function",
    "router",
    "endpoint",
)

_WRITE_HINTS = (
    "write",
    "create",
    "update",
    "modify",
    "fix",
    "patch",
    "change",
)

_TERMINAL_HINTS = (
    "run command",
    "execute command",
    "terminal",
    "shell",
    "build",
    "test",
)


@dataclass(slots=True)
class PlannerSignals:
    search: bool = False
    read: bool = False
    memory: bool = False
    rag: bool = False
    write: bool = False
    terminal: bool = False
    specific_path: str | None = None
    search_query: str | None = None


class WorkflowPlanner:
    """
    Deterministic planner that converts a query into a strict JSON workflow plan.
    """

    def build_plan(
        self,
        query: str,
        intent: IntentDecision | IntentType | None = None,
        available_tools: list[str] | None = None,
    ) -> WorkflowPlan:
        query = query.strip()
        signals = self._detect_signals(query)
        steps: list[WorkflowStepPlan] = []
        step_id = 1

        def add_step(tool: str, args: dict[str, Any] | None = None, depends_on: list[int] | None = None,
                     fallback_tools: list[str] | None = None, critical: bool = True, description: str | None = None):
            nonlocal step_id
            steps.append(
                WorkflowStepPlan(
                    id=step_id,
                    tool=tool,
                    args=args or {},
                    depends_on=depends_on or [],
                    fallback_tools=fallback_tools or [],
                    critical=critical,
                    description=description,
                )
            )
            step_id += 1
            return step_id - 1

        # Independent context collection can run in parallel.
        search_step_id: int | None = None
        read_step_id: int | None = None

        if signals.memory or (intent is not None and self._intent_requires_memory(intent)):
            add_step(
                "memory_search",
                args={"query": query},
                fallback_tools=[],
                critical=False,
                description="Recall relevant prior context.",
            )

        if signals.search:
            search_query = signals.search_query or query
            search_step_id = add_step(
                "search_files",
                args={"query": search_query},
                fallback_tools=["file_search"],
                critical=True,
                description="Find candidate files or references.",
            )

        if signals.rag or (intent is not None and self._intent_prefers_rag(intent)):
            add_step(
                "rag_retrieve",
                args={"query": query},
                fallback_tools=["rag"],
                critical=False,
                description="Retrieve contextual codebase knowledge.",
            )

        if signals.read:
            read_args = self._build_read_args(signals, search_step_id)
            depends_on = [search_step_id] if search_step_id is not None else []
            if signals.specific_path and search_step_id is None:
                depends_on = []
            read_step_id = add_step(
                "read_file",
                args=read_args,
                depends_on=depends_on,
                fallback_tools=[],
                critical=True,
                description="Read the most relevant file or file path.",
            )

        if signals.write:
            write_depends = [read_step_id] if read_step_id is not None else []
            add_step(
                "write_file",
                args=self._build_write_args(query, signals),
                depends_on=write_depends,
                fallback_tools=[],
                critical=True,
                description="Apply a requested workspace modification.",
            )

        if signals.terminal:
            add_step(
                "terminal_execute",
                args={"command": self._extract_command(query)},
                depends_on=[],
                fallback_tools=[],
                critical=False,
                description="Execute an explicit terminal command.",
            )

        # If the query is descriptive and no direct file read was scheduled,
        # we still allow a final knowledge step to precede synthesis.
        if not steps and (signals.rag or signals.read):
            add_step(
                "rag_retrieve",
                args={"query": query},
                fallback_tools=["rag"],
                critical=False,
                description="Fallback knowledge retrieval.",
            )

        return WorkflowPlan(goal=self._describe_goal(query), steps=steps)

    def _detect_signals(self, query: str) -> PlannerSignals:
        q = query.lower()
        signals = PlannerSignals()

        signals.search = self._contains_any(q, _SEARCH_HINTS)
        signals.read = self._contains_any(q, _READ_HINTS) or self._looks_like_file_request(q)
        signals.memory = self._contains_any(q, _MEMORY_HINTS)
        signals.rag = self._contains_any(q, _RAG_HINTS)
        signals.write = self._contains_any(q, _WRITE_HINTS) and not self._contains_any(q, ("explain", "summarize"))
        signals.terminal = self._contains_any(q, _TERMINAL_HINTS)
        signals.specific_path = self._extract_path(query)
        signals.search_query = self._extract_search_query(query)

        if signals.specific_path:
            signals.read = True
            signals.search = False

        if signals.search and signals.specific_path:
            signals.search = False

        if self._explicit_find_then_explain(q):
            signals.search = True
            signals.read = True

        return signals

    def _contains_any(self, text: str, needles: tuple[str, ...]) -> bool:
        return any(token in text for token in needles)

    def _looks_like_file_request(self, query: str) -> bool:
        return bool(re.search(r"\b[\w./-]+\.[A-Za-z0-9]{1,6}\b", query))

    def _extract_path(self, query: str) -> str | None:
        quoted = re.search(r'["\'`](.+?)["\'`]', query)
        if quoted:
            candidate = quoted.group(1).strip("\"'`")
            if "/" in candidate or "." in candidate:
                return candidate

        path_match = re.search(r"\b([\w./-]+\.[A-Za-z0-9]{1,6})\b", query)
        if path_match:
            return path_match.group(1)

        return None

    def _extract_search_query(self, query: str) -> str | None:
        patterns = [
            r"file containing (.+?)(?:$| and | then |,|\.| explaining| explain)",
            r"find (.+?)(?:$| and | then |,|\.| explaining| explain)",
            r"search for (.+?)(?:$| and | then |,|\.| explaining| explain)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query, flags=re.IGNORECASE)
            if match:
                extracted = match.group(1).strip(" \"'`")
                return extracted or None
        return None

    def _explicit_find_then_explain(self, query: str) -> bool:
        return "find" in query and "explain" in query

    def _build_read_args(self, signals: PlannerSignals, search_step_id: int | None) -> dict[str, Any]:
        if signals.specific_path:
            return {"path": signals.specific_path}
        if search_step_id is not None:
            return {"path": f"{{{{step{search_step_id}.result.primary_path}}}}"}
        return {"path": ""}

    def _build_write_args(self, query: str, signals: PlannerSignals) -> dict[str, Any]:
        content = query
        if signals.specific_path:
            return {
                "path": signals.specific_path,
                "content": content,
                "overwrite": True,
            }
        return {
            "path": self._extract_path(query) or "workspace_output.txt",
            "content": content,
            "overwrite": True,
        }

    def _extract_command(self, query: str) -> str:
        explicit = re.search(r"(?:run command|execute command|terminal|shell)\s*:?\s*(.+)$", query, flags=re.IGNORECASE)
        if explicit:
            return explicit.group(1).strip()
        return query

    def _describe_goal(self, query: str) -> str:
        q = query.strip().lower()
        if self._contains_any(q, _SEARCH_HINTS) and self._contains_any(q, _READ_HINTS):
            return "retrieve and explain file"
        if self._contains_any(q, _WRITE_HINTS):
            return "modify workspace artifact"
        if self._contains_any(q, _TERMINAL_HINTS):
            return "execute terminal task"
        if self._contains_any(q, _RAG_HINTS):
            return "retrieve and synthesize codebase context"
        return "answer user request"

    def _intent_requires_memory(self, intent: IntentDecision | IntentType) -> bool:
        if isinstance(intent, IntentDecision):
            return intent.requires_tools or intent.intent == IntentType.RAG
        return intent in {IntentType.RAG, IntentType.TOOL, IntentType.SYSTEM}

    def _intent_prefers_rag(self, intent: IntentDecision | IntentType) -> bool:
        if isinstance(intent, IntentDecision):
            return intent.intent in {IntentType.RAG, IntentType.SYSTEM}
        return intent in {IntentType.RAG, IntentType.SYSTEM}
