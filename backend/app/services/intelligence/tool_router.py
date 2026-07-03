"""Intent-based tool routing — determines when to use tools before the LLM decides.

Works with ALL model sizes:
- Small models (3-8B): may ignore TOOL_CALL syntax entirely. The router
  detects obvious tool-needing intents and forces tool execution.
- Large models (14B+): can decide tool usage via native function calling.
  The router acts as a safety net and pre-flight validation.

Strategy:
1. Keyword/pattern matching for high-confidence tool triggers
2. LLM classification for ambiguous cases (only when keyword match is weak)
3. Native Ollama tool_calls for models that support them
4. Text-based TOOL_CALL: syntax for models that don't
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolIntent:
    """Result of intent analysis — which tools to offer and which to force."""

    tools_needed: list[str] = field(default_factory=list)
    forced_tool: str | None = None
    forced_args: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    reasoning: str = ""


# ── Keyword patterns for high-confidence tool triggers ──────────────

_SEARCH_PATTERNS = [
    r"\bsearch\s+(?:the\s+)?(?:web|internet|google|online)\b",
    r"\b(?:look|look\s+up|find)\s+(?:it|this|that|out)\s+(?:on|in|at)\s+(?:the\s+)?(?:web|internet|google|online)\b",
    r"\bwhat(?:'s| is| are) (?:the )?(?:latest|newest|current|recent)\b",
    r"\btell me about\b",
    r"\bwhat (?:is|are|was|were) .*\b(?:in 2024|in 2025|in 2026|today|now|currently)\b",
    r"\bhow (?:do|does|to|is) .*\b(?:in 2024|in 2025|in 2026)\b",
    # Common typos — "webserch", "searhc", etc.
    r"\bwebserch\b",
    r"\bsearhc\b",
    r"\bwe[bs]earch\b",
    r"\b(?:google|ddg|duckduckgo|bing|yahoo)\b",
]

_WRITE_FILE_PATTERNS = [
    r"\b(?:write|save|create)\s+(?:a\s+)?(?:file|essay|document|report|note|letter|script)\b",
    r"\bsave\s+(?:this|it|that)\s+(?:to|in|as)\b",
    r"\bwrite\s+(?:this|it|that)\s+(?:to|into|as)\b",
    r"\bcreate\s+(?:a\s+)?(?:file|document)\s+(?:named?|called?|at|in)\b",
]

_EXEC_PATTERNS = [
    r"\b(?:run|execute|install|pip|npm|apt|brew|docker)\b",
    r"\b(?:compile|build|make|test|deploy)\s+",
    r"\b(?:check|show)\s+(?:disk|memory|cpu|process|port|pid)\b",
    r"\b(?:list|show)\s+(?:all\s+)?(?:files|directories|folders)\b",
]

_READ_FILE_PATTERNS = [
    r"\b(?:read|open|show|cat|display)\s+(?:the\s+)?(?:file|content)\b",
    r"\bwhat(?:'s| is) (?:in|inside)\s+(?:the\s+)?(?:file|document)\b",
]

_GIT_PATTERNS = [
    r"\b(?:git\s+log|git\s+diff|git\s+status|git\s+show)\b",
    r"\b(?:what|show)\s+(?:did|has)\s+.*(?:commit|change|push)\b",
    r"\b(?:recent|latest|last)\s+(?:commits?|changes?)\b",
]


def _match_patterns(text: str, patterns: list[str]) -> bool:
    """Check if text matches any of the given regex patterns."""
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


def classify_intent_tools(message: str) -> ToolIntent:
    """Classify which tools a message needs based on keyword patterns.

    Returns high-confidence tool assignments for obvious cases.
    Returns empty tools_needed for ambiguous cases (let LLM decide).
    """
    lower = message.lower()

    # ── Web search: strong signals ──────────────────────────────
    if _match_patterns(message, _SEARCH_PATTERNS):
        return ToolIntent(
            tools_needed=["web_search"],
            confidence=0.9,
            reasoning="Message requests web information",
        )

    # ── File writing ───────────────────────────────────────────
    if _match_patterns(message, _WRITE_FILE_PATTERNS):
        # Try to extract the file path
        path_match = re.search(
            r"(?:to|in|as|at|named?|called?)\s+[\"']?([^\s\"']+)[\"']?",
            lower,
        )
        args: dict[str, str] = {}
        if path_match:
            args["path"] = path_match.group(1)
        return ToolIntent(
            tools_needed=["write_file"],
            forced_tool="write_file",
            forced_args=args,
            confidence=0.85,
            reasoning="Message requests file creation",
        )

    # ── Shell execution ────────────────────────────────────────
    if _match_patterns(message, _EXEC_PATTERNS):
        # Extract the command — usually everything after "run"/"execute"
        cmd_match = re.search(r"(?:run|execute)\s+(.+?)(?:\s*$)", lower)
        args = {}
        if cmd_match:
            args["command"] = cmd_match.group(1).strip()
        return ToolIntent(
            tools_needed=["exec_command"],
            confidence=0.8,
            reasoning="Message requests command execution",
        )

    # ── File reading ───────────────────────────────────────────
    if _match_patterns(message, _READ_FILE_PATTERNS):
        path_match = re.search(
            r"(?:file|content)\s+(?:called?|named?|at|in|of)?\s*[\"']?([^\s\"']+)[\"']?",
            lower,
        )
        args = {}
        if path_match:
            args["path"] = path_match.group(1)
        return ToolIntent(
            tools_needed=["read_file"],
            confidence=0.8,
            reasoning="Message requests file reading",
        )

    # ── Git operations ─────────────────────────────────────────
    if _match_patterns(message, _GIT_PATTERNS):
        if re.search(r"\bgit\s+log\b", lower) or re.search(r"recent|latest|last.*commit", lower):
            return ToolIntent(
                tools_needed=["git_log"],
                confidence=0.85,
                reasoning="Message requests git log",
            )
        if re.search(r"\bgit\s+diff\b", lower) or re.search(r"what.*change", lower):
            return ToolIntent(
                tools_needed=["git_diff"],
                confidence=0.85,
                reasoning="Message requests git diff",
            )
        if re.search(r"\bgit\s+status\b", lower):
            return ToolIntent(
                tools_needed=["git_status"],
                confidence=0.9,
                reasoning="Message requests git status",
            )
        return ToolIntent(
            tools_needed=["git_log", "git_status"],
            confidence=0.7,
            reasoning="Message requests git info (unclear which)",
        )

    # ── No tool needed — let LLM decide naturally ──────────────
    return ToolIntent(
        tools_needed=[],
        confidence=0.5,
        reasoning="No obvious tool trigger detected",
    )


def build_tool_choice_hint(intent: ToolIntent) -> str:
    """Build a hint for the LLM about what tools to use.

    Injected into the system prompt when intent router detects a tool need.
    Helps small models that might otherwise ignore the tool list.
    """
    if not intent.tools_needed:
        return ""

    if intent.forced_tool:
        args_str = ", ".join(f"{k}={v!r}" for k, v in intent.forced_args.items())
        return (
            f"\n\nIMPORTANT: This message requires the {intent.forced_tool} tool. "
            f"You MUST use it. Format: TOOL_CALL: {intent.forced_tool}({args_str})\n"
        )

    tool_list = ", ".join(intent.tools_needed)
    return f"\n\nHINT: This message likely needs these tools: {tool_list}. Use TOOL_CALL format if appropriate.\n"
