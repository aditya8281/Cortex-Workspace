"""Single streaming agent loop — replaces the legacy Planner→Executor pattern.

This is the core of V1 Phase 2. A single async generator handles intent
classification, context management, LLM streaming, tool execution, stall
detection, compaction, and completion verification — all in one loop.

Usage:
    from backend.app.agents.loop import agent_loop
    from backend.app.agents.tools import get_tool_registry, default_policy

    async for event in agent_loop(
        message="What files changed in the last commit?",
        conversation_id="conv-123",
        user=user,
        registry=get_tool_registry(),
        policy=default_policy(),
    ):
        if isinstance(event, AgentMessage):
            print(f"AI: {event.text}")
        elif isinstance(event, ToolCall):
            print(f"Tool: {event.name}({event.args})")
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncGenerator
from typing import Any

from backend.app.agents.compactor import compact_context, estimate_token_count
from backend.app.agents.events import (
    AgentEvent,
    AgentMessage,
    Compaction,
    Done,
    Thinking,
    ToolCall,
    ToolDenied,
    ToolResult,
)
from backend.app.agents.intent import casual_response, classify_intent
from backend.app.agents.stall import StallDetector
from backend.app.agents.tools.policy import ToolPolicy
from backend.app.agents.tools.registry import ToolRegistry
from backend.app.agents.verifier import verify_completion
from backend.app.services.intelligence.llm.provider import LLMMessage

logger = logging.getLogger(__name__)

async def _unload_model(model_name: str) -> None:
    """Run 'ollama stop' to free GPU VRAM after an LLM response.

    Runs in background — never blocks the agent loop.
    Called automatically after llm_chat() returns.
    This is critical for GPUs with limited VRAM (e.g. 6GB).
    """
    from backend.app.core.config import settings

    if not settings.VRAM_CLEANUP or not model_name or model_name == "unknown":
        return

    # Extract short model name (e.g. "qwen3:8b" from full identifier)
    name = model_name.split("/")[-1].split(":")[0]
    full_name = model_name
    if ":" not in full_name and name:
        full_name = name

    try:
        proc = await asyncio.create_subprocess_exec(
            "ollama", "stop", full_name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=5)
        logger.debug("VRAM cleanup: stopped model %s", full_name)
    except (asyncio.TimeoutError, FileNotFoundError, ProcessLookupError):
        pass  # Non-critical — best effort


# Maximum iterations before the loop forces a final answer.
# Safety valve to prevent infinite loops.
MAX_ITERATIONS = 25

# Fraction of context window that triggers compaction.
COMPACTION_THRESHOLD = 0.85

# Default context window size (tokens) when model limits are unknown.
DEFAULT_CONTEXT_WINDOW = 4096

# System prompt for the agent loop.
_SYSTEM_PROMPT = (
    "You are CORTEX, a local-first AI assistant.\n\n"
    "## Identity & Purpose\n"
    "You have tools — think of them as your hands. You read files, write code, search the web,\n"
    "run commands, access knowledge. Use these tools naturally to accomplish the task,\n"
    "like a capable developer using their IDE.\n\n"
    "## Tool Calling Format\n"
    "TOOL_CALL: tool_name(param=value, param2=value2)\n\n"
    "String values in quotes: TOOL_CALL: read_file(path=\"src/main.py\")\n"
    "Numbers/booleans bare: TOOL_CALL: git_log(count=5)\n"
    "Multiple tools per response? Use multiple TOOL_CALL lines.\n\n"
    "## Core Behavior\n"
    "1. Think step-by-step inside <think> tags before each action.\n"
    "2. Explain what you're doing before calling a tool.\n"
    "3. After results, synthesize into a clear response.\n"
    "4. Need more info? Call more tools.\n"
    "5. Enough info? Give a complete answer.\n"
    "6. Be concise but thorough — show your work where it matters.\n"
    "7. Do NOT call the same tool with the same arguments more than once.\n"
    "8. If a tool is DENIED, do NOT retry it. Find a different approach.\n\n"
    "## Your Tool Ecosystem (Your Hands)\n"
    "You have these capabilities:\n"
    "  📂 Files: read, write, edit, copy, move, delete, mkdir, search_path, list_directory\n"
    "  💻 Code: grep, git_log, git_diff, git_status, git_show, get_repo_info\n"
    "  🌐 Web: web_search (search + auto-extract content), web_fetch\n"
    "  🧠 Knowledge: search_knowledge, current_datetime\n"
    "  ⚙️ System: exec_command, list_available_tools\n\n"
    "Some tools need approval (write_file, edit_file, exec_command, delete_file, etc.).\n"
    "Propose them — the system approves or denies. If DENIED, never retry.\n\n"
    "## Handling Tool Denials\n"
    "When a tool is denied:\n"
    "  - ACCEPT the denial. Do NOT retry the same tool.\n"
    "  - Find an alternative approach that doesn't use the denied tool.\n"
    "  - If the task is impossible without it, explain what was denied\n"
    "    and suggest what the user can do instead.\n"
    "  - Repeatedly calling a denied tool triggers a stall detector\n"
    "    that forces a final answer.\n\n"
    "## Discovery-First Pattern\n"
    "Do NOT assume file paths exist. Always discover first:\n"
    "  - search_path(name) -> find files/dirs by name\n"
    "  - list_directory(path) -> verify contents\n"
    "  - read_file(path) -> read content\n"
    "  - write_file / edit_file -> modify after verifying\n\n"
    "Example: write to Desktop/test.txt:\n"
    "  search_path(\"Desktop\") -> find Desktop path\n"
    "  list_directory(path/Desktop) -> verify location\n"
    "  write_file(path/Desktop/test.txt, content) -> write\n\n"
    "## Multi-Tool Orchestration\n"
    "Chain tools naturally. A task needs 3-5 calls:\n"
    "  - Discover (search_path / list_directory)\n"
    "  - Gather context (read_file / grep / git_log / web_search)\n"
    "  - Take action (write_file / edit_file / exec_command)\n"
    "  - Verify (read_file / git_diff / git_status)\n\n"
    "Example: find and fix a bug:\n"
    "  1. grep_files -> find the bug location\n"
    "  2. read_file -> read the relevant code\n"
    "  3. git_log -> see when it was introduced\n"
    "  4. edit_file -> fix the bug\n"
    "  5. git_diff -> verify the fix\n\n"
    "## Self-Correction\n"
    "If a tool returns unexpected:\n"
    "  1. Path or name wrong? search_path to find it\n"
    "  2. Try alternatives if first attempt fails\n"
    "  3. Report what worked and what didn't\n"
    "  4. Wrong args? Retry with correct ones"
)


async def agent_loop(
    message: str,
    conversation_id: str,
    user: Any,
    registry: ToolRegistry,
    policy: ToolPolicy,
    model: str = "default",
    max_iterations: int = MAX_ITERATIONS,
    llm_chat: Any = None,
) -> AsyncGenerator[AgentEvent, None]:
    """Single streaming agent loop.

    Args:
        message: The user's input message.
        conversation_id: Unique conversation identifier.
        user: The user object (must have .id).
        registry: ToolRegistry with registered tools.
        policy: ToolPolicy for allow/deny/ask decisions.
        model: Model override for LLM calls.
        max_iterations: Maximum loop iterations before forcing answer.
        llm_chat: Async chat function (e.g., llm_manager.chat). If None,
                  imports llm_manager internally.

    Yields:
        AgentEvent instances: AgentMessage, ToolCall, ToolResult, ToolDenied,
        Compaction, Thinking, Done.
    """
    # Resolve LLM chat function
    if llm_chat is None:
        from backend.app.services.intelligence.llm.manager import llm_manager

        llm_chat = llm_manager.chat

    # 1. Classify intent
    intent = classify_intent(message)

    # Casuals get a fast-path response
    if intent == "casual":
        yield AgentMessage(text=casual_response(message))
        yield Done(summary="Casual conversation handled", status="completed")
        return

    yield Thinking(text=f"Classified intent: {intent}")

    # Admin and continuation currently also go through the loop
    # (admin-specific fast path could be added later)

    # 2. Initialize stall detector
    stall_detector = StallDetector()

    # 3. Build conversation history
    history: list[dict[str, str]] = [
        {"role": "user", "content": message},
    ]

    # Track iterations for tool policy iteration-awareness
    iteration = 0
    tool_calls_summary: list[dict[str, Any]] = []

    # 4. Main streaming loop
    while iteration < max_iterations:
        iteration += 1

        # Check stall detection
        if stall_detector.is_stalled():
            yield Thinking(text="Stall detected — forcing answer")
            forced_prompt = stall_detector.force_answer_prompt()
            history.append({"role": "user", "content": forced_prompt})
            stall_detector.reset()

        # Build messages for LLM
        llm_messages = [
            LLMMessage(role="system", content=_SYSTEM_PROMPT),
        ]

        # Add contexts: tool schemas as a description of available tools
        tool_info = _format_tool_info(registry)
        if tool_info:
            llm_messages.append(LLMMessage(role="system", content=f"Available tools:\n{tool_info}"))

        # Add conversation history
        for entry in history:
            llm_messages.append(LLMMessage(role=entry["role"], content=entry["content"]))

        # Check compaction need
        token_est = estimate_token_count(history, approx_chars_per_token=4.0)
        if token_est > int(DEFAULT_CONTEXT_WINDOW * COMPACTION_THRESHOLD):
            yield Thinking(text=f"Context at ~{token_est} tokens — compacting")
            summary = await compact_context(history, llm_chat=llm_chat, model=model)
            yield Compaction(summary=summary)
            # Replace history with compacted version
            # Preserve the original user message so the LLM knows its task
            user_msg = (
                history[0] if history and history[0].get("role") == "user" else {"role": "user", "content": message}
            )
            history = [
                {"role": "system", "content": f"Previous context summary:\n{summary}"},
                user_msg,
            ]
            token_est = 0

        try:
            # Call LLM
            response = await llm_chat(
                messages=llm_messages,
                model=model,
                max_tokens=8192,
            )

            # Free GPU VRAM after each LLM response (runs in background)
            asyncio.ensure_future(_unload_model(response.model))

            content = response.content.strip()
            if not content:
                logger.warning("Empty LLM response at iteration %d", iteration)
                if iteration >= max_iterations:
                    break
                continue

            # Check for tool calls in the response
            tool_calls = _parse_tool_calls(content)

            if tool_calls:
                # Remove tool call syntax from what we show the user
                user_visible = _strip_tool_calls(content)
                if user_visible:
                    yield AgentMessage(text=user_visible)
                    # Preserve assistant reasoning in history so the next iteration
                    # has context of what the model was thinking.
                    history.append({"role": "assistant", "content": user_visible})

                for tc in tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc.get("args", {})

                    # Coerce arg types based on tool schema
                    tool_obj = registry.get(tool_name)
                    if tool_obj:
                        tool_args = _coerce_args(tool_args, tool_obj.schema)

                    yield Thinking(text=f"Calling tool: {tool_name}")
                    yield ToolCall(name=tool_name, args=tool_args)

                    # Check policy
                    decision = policy.evaluate(tool_name, iteration)
                    if decision == "deny":
                        stall_detector.record_denial(tool_name)
                        yield ToolDenied(name=tool_name, reason="Denied by policy")
                        history.append(
                            {
                                "role": "tool",
                                "content": f"[Tool {tool_name} DENIED by policy. "
                                f"Do not retry — this tool is permanently unavailable. "
                                f"Find an alternative approach.]",
                            }
                        )
                        continue

                    if decision == "ask":
                        stall_detector.record_denial(tool_name)
                        yield ToolDenied(
                            name=tool_name,
                            reason="Requires approval — not available in this mode",
                        )
                        history.append(
                            {
                                "role": "tool",
                                "content": f"[Tool {tool_name} requires approval — DENIED. "
                                f"Do not retry. Find an alternative approach without this tool.]",
                            }
                        )
                        continue

                    # Execute the tool
                    try:
                        result = await registry.execute(tool_name, **tool_args)
                        yield ToolResult(name=tool_name, result=result)
                        history.append(
                            {
                                "role": "tool",
                                "content": f"[{tool_name} returned]: {result[:2000]}",
                            }
                        )
                        stall_detector.record_call(tool_name, tool_args)
                        tool_calls_summary.append({"name": tool_name, "args": tool_args})
                    except ValueError as exc:
                        error_msg = f"Tool '{tool_name}' not found"
                        yield ToolResult(name=tool_name, result=error_msg)
                        history.append({"role": "tool", "content": error_msg})
                        logger.warning("Tool call failed: %s", exc)
                    except Exception as exc:
                        error_msg = f"Tool '{tool_name}' execution failed"
                        yield ToolResult(name=tool_name, result=error_msg)
                        history.append({"role": "tool", "content": error_msg})
                        logger.error("Tool '%s' execution error: %s", tool_name, exc, exc_info=True)
            else:
                # Pure text response
                yield AgentMessage(text=content)
                history.append({"role": "assistant", "content": content})

            # Check for natural completion signals
            if _is_completion_signal(content):
                logger.info("Agent signaled completion at iteration %d", iteration)
                break

        except Exception as exc:
            error_msg = f"LLM call failed: {exc}"
            logger.error("LLM error at iteration %d: %s", iteration, exc)
            yield AgentMessage(text=f"I encountered an error: {exc}")
            break

    # 5. Verify completion
    final_response = history[-1].get("content", "") if history else ""
    verdict = await verify_completion(
        original_message=message,
        conversation_history=history,
        final_response=final_response,
        llm_chat=llm_chat,
    )

    # 6. Emit Done
    yield Done(
        summary=verdict.summary or f"Completed after {iteration} iterations",
        status="completed" if verdict.complete else ("failed" if iteration < max_iterations else "incomplete"),
    )

    logger.info(
        "Agent loop finished: intent=%s, iterations=%d, complete=%s, tool_calls=%d",
        intent,
        iteration,
        verdict.complete,
        len(tool_calls_summary),
    )


def _format_tool_info(registry: ToolRegistry) -> str:
    """Format registered tools as a description string for the LLM."""
    tools = registry.get_all()
    if not tools:
        return ""
    lines: list[str] = []
    for t in tools:
        params = _describe_schema_params(t.schema)
        lines.append(f"  - {t.name}: {t.description}{params}")
    return "\n".join(lines)


def _coerce_args(args: dict[str, str], schema: dict) -> dict[str, Any]:
    """Coerce string argument values to types declared in the tool schema.

    Tool call args arrive as strings from TOOL_CALL parsing. This uses the
    tool's JSON schema parameter types to coerce int/float/bool/None values.
    """
    if not args or not schema:
        return args
    try:
        params = schema.get("function", {}).get("parameters", {}).get("properties", {})
        if not params:
            return args
        coerced: dict[str, Any] = {}
        for key, val in args.items():
            prop = params.get(key, {})
            ptype = prop.get("type", "string")
            if val.lower() in ("none", "null", ""):
                coerced[key] = None
            elif ptype == "integer":
                coerced[key] = int(val)
            elif ptype == "number":
                coerced[key] = float(val)
            elif ptype == "boolean":
                coerced[key] = val.lower() in ("true", "1", "yes")
            else:
                coerced[key] = val
        return coerced
    except (ValueError, TypeError):
        return args


def _describe_schema_params(schema: dict) -> str:
    """Extract parameter descriptions from a tool's JSON schema."""
    try:
        props = schema.get("function", {}).get("parameters", {}).get("properties", {})
        if not props:
            return ""
        param_desc = ", ".join(f"{name}: {prop.get('description', name)}" for name, prop in props.items())
        return f" ({param_desc})"
    except Exception:
        return ""


# Matches TOOL_CALL directives. Handles:
#   TOOL_CALL: web_search(query="...")
#   TOOL_CALL:web_search(query="...")       (no space after colon)
#   `TOOL_CALL: web_search(...)`            (backtick-wrapped)
#   TOOL_CALL web_search(...)               (missing colon)
#   tool_call: web_search(...)              (lowercase)
#   TOOL_CALL: web_search (query = "...")   (spaces around name/parens)
# Argument extraction uses paren-depth counting to handle nested parens.
_TOOL_CALL_START_RE = re.compile(
    r"`*\s*TOOL_CALL\s*:?\s*(\w+)\s*\(",
    re.IGNORECASE,
)


def _extract_paren_block(text: str, start: int) -> tuple[str, int] | None:
    """Extract a balanced parenthesized block starting at text[start]=='('.

    Returns (content_inside_parens, end_position_after_closing_paren)
    or None if unbalanced.
    """
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
    return None


def _parse_tool_calls(text: str) -> list[dict]:
    """Parse TOOL_CALL directives from LLM response text.

    Parses format: TOOL_CALL: tool_name(param=value, param2=value2)
    Uses paren-depth counting so quoted values with parens work
    (e.g. path="some/file(1).txt").
    """
    result: list[dict] = []
    pos = 0
    while True:
        match = _TOOL_CALL_START_RE.search(text, pos)
        if not match:
            break
        name = match.group(1)
        block = _extract_paren_block(text, match.end() - 1)
        if block is None:
            pos = match.end()
            continue
        args_str, end_pos = block
        args = _parse_args(args_str)
        result.append({"name": name, "args": args})
        pos = end_pos
    return result


def _parse_args(args_str: str) -> dict[str, str]:
    """Parse key=value arguments from a tool call string.

    Handles quoted strings and simple values.
    """
    if not args_str.strip():
        return {}
    args: dict[str, str] = {}
    # Split on commas not inside quotes
    parts = _split_args(args_str)
    for part in parts:
        if "=" in part:
            key, val = part.split("=", 1)
            key = key.strip()
            val = val.strip().strip("\"'")
            if key:
                args[key] = val
    return args


def _split_args(args_str: str) -> list[str]:
    """Split argument string on commas, respecting quoted strings."""
    parts: list[str] = []
    current: list[str] = []
    in_quote = False
    quote_char = ""
    for ch in args_str:
        if ch in ("'", '"'):
            if in_quote and ch == quote_char:
                in_quote = False
            elif not in_quote:
                in_quote = True
                quote_char = ch
            current.append(ch)
        elif ch == "," and not in_quote:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _strip_tool_calls(text: str) -> str:
    """Remove TOOL_CALL directives from text, leaving only user-visible content.

    Uses paren-depth counting to handle nested parens in arguments.
    Also strips surrounding backticks and code-block fences
    (`` `TOOL_CALL: ...()``, ``````TOOL_CALL: ...()``````) cleanly.
    """
    result_parts: list[str] = []
    pos = 0
    while True:
        match = _TOOL_CALL_START_RE.search(text, pos)
        if not match:
            result_parts.append(text[pos:])
            break
        # Append text before this TOOL_CALL (excluding any opening backticks/fence)
        before = text[pos : match.start()]
        # Strip trailing backticks from "before" (the leading fence that the
        # regex's `\`*` prefix consumed as part of the match)
        result_parts.append(before.rstrip("`"))
        block = _extract_paren_block(text, match.end() - 1)
        if block is None:
            pos = match.end()
            continue
        _, end_pos = block
        # Skip trailing whitespace after the call
        while end_pos < len(text) and text[end_pos] in " \t\n":
            end_pos += 1
        # Skip trailing backtick(s) if present (matching the leading ones)
        while end_pos < len(text) and text[end_pos] == "`":
            end_pos += 1
        pos = end_pos
    return "".join(result_parts).strip()


def _is_completion_signal(content: str) -> bool:
    """Check if the LLM indicated task completion."""
    lower = content.strip().lower().rstrip(".,!?;: \t\n")
    # If the last paragraph indicates completion
    return lower.endswith(("task complete", "all done", "finished"))
