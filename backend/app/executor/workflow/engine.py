from __future__ import annotations

import asyncio
import copy
import json
import logging
import re
import time
from typing import Any

from backend.app.ai.llm_router import LLMRouter
from backend.app.executor.context_compiler import ContextCompiler
from backend.app.executor.tracer import ExecutionTracer
from backend.app.executor.tool_registry import ToolRegistry
from backend.app.executor.workflow.models import (
    WorkflowGraph,
    WorkflowNode,
    WorkflowState,
    WorkflowStepLog,
)
from backend.app.tools.base import ToolContext, ToolResult
from backend.app.state.models import EventType, SystemEvent


logger = logging.getLogger(__name__)


class WorkflowExecutionEngine:
    """
    Executes a validated workflow DAG with retries, fallbacks, and shared state.
    """

    def __init__(self, executor):
        self.executor = executor
        self.registry: ToolRegistry = executor.tool_registry
        self.tracer: ExecutionTracer = executor.tracer
        self.state_manager = executor.state
        self.llm = LLMRouter()

    async def execute(
        self,
        query: str,
        graph: WorkflowGraph,
        user_id: int | None = None,
        intent: Any = None,
        history: list | None = None,
        llm_model: str | None = None,
        embedding_model: str | None = None,
        vector_db: str | None = None,
        inference_engine: str | None = None,
        code_parsing: str | None = None,
        api_key: str | None = None,
        api_base_url: str | None = None,
        context_items: list | None = None,
    ) -> dict[str, Any]:
        execution_id = self.tracer.create_session()
        workflow_state = WorkflowState(
            execution_id=execution_id,
            query=query,
            user_id=user_id,
            intent=intent,
            llm_model=llm_model,
            embedding_model=embedding_model,
            vector_db=vector_db,
            inference_engine=inference_engine,
            code_parsing=code_parsing,
            api_key=api_key,
            api_base_url=api_base_url,
            history=history,
            context_items=context_items,
            permissions={
                "write_file": False,
                "terminal_execute": False,
            },
        )
        runtime_state = workflow_state.to_runtime_state()

        self.state_manager.set_execution_id(execution_id)
        self.state_manager.emit_event(
            SystemEvent(
                type=EventType.TOOL_EXECUTED,
                payload={
                    "stage": "workflow_start",
                    "execution_id": execution_id,
                    "query": query,
                    "step_count": len(graph.nodes),
                },
                source="WorkflowExecutionEngine",
            ),
            execution_id=execution_id,
        )

        step_outputs: dict[str, ToolResult] = {}
        stopped = False
        stop_reason = None

        try:
            for layer in graph.layers:
                if stopped:
                    break

                ready_nodes = [graph.get_node(node_id) for node_id in layer]
                ready_nodes = [node for node in ready_nodes if node is not None]

                results = await asyncio.gather(
                    *[
                        self._execute_node(
                            execution_id=execution_id,
                            node=node,
                            state=runtime_state,
                            step_outputs=step_outputs,
                            query=query,
                            user_id=user_id,
                        )
                        for node in ready_nodes
                    ]
                )

                for node, result in zip(ready_nodes, results):
                    tool_result = result["result"]
                    step_outputs[node.id] = tool_result
                    runtime_state["step_results"][node.id] = tool_result.to_dict() if isinstance(tool_result, ToolResult) else tool_result
                    runtime_state["completed_steps"].append(node.id)
                    runtime_state["execution_logs"].append(result["log"])

                    if result["retrieved_file"]:
                        runtime_state["retrieved_files"].append(result["retrieved_file"])

                    if result["memory_context"]:
                        runtime_state["retrieved_context"].setdefault("memory_search", []).append(result["memory_context"])

                    if isinstance(tool_result, ToolResult) and tool_result.status == "error":
                        error_payload = {
                            "step_id": node.id,
                            "tool": node.tool,
                            "error": tool_result.meta.get("error") or tool_result.reason or "tool_error",
                        }
                        runtime_state["errors"].append(error_payload)
                        if node.critical:
                            stopped = True
                            stop_reason = error_payload["error"]

                if stopped:
                    break

            memory_context = self._build_memory_context(runtime_state)
            tool_results = [value for value in step_outputs.values() if isinstance(value, ToolResult)]
            summary = self._build_summary(graph, runtime_state, tool_results, stop_reason)
            runtime_state["summary"] = summary

            final_response = await self._generate_response(
                query=query,
                runtime_state=runtime_state,
                tool_results=tool_results,
                memory_context=memory_context,
                llm_model=llm_model,
            )
            runtime_state["final_response"] = final_response

            self.state_manager.emit_event(
                SystemEvent(
                    type=EventType.EXECUTION_COMPLETED,
                    payload={
                        "execution_id": execution_id,
                        "query": query,
                        "status": "failed" if runtime_state["errors"] else "success",
                        "step_count": len(graph.nodes),
                        "executed_steps": len(runtime_state["completed_steps"]),
                        "error_count": len(runtime_state["errors"]),
                    },
                    source="WorkflowExecutionEngine",
                ),
                execution_id=execution_id,
            )

            return {
                "execution_id": execution_id,
                "query": query,
                "final_response": final_response,
                "memory": memory_context,
                "tool_results": tool_results,
                "workflow_state": runtime_state,
                "workflow_summary": summary,
                "routing_info": {
                    "workflow_summary": summary,
                    "execution_graph": {
                        "nodes": [
                            {
                                "id": node.id,
                                "step_id": node.step_id,
                                "tool": node.tool,
                                "depends_on": node.depends_on,
                                "critical": node.critical,
                                "fallback_tools": node.fallback_tools,
                            }
                            for node in graph.nodes
                        ],
                        "layers": graph.layers,
                    },
                },
            }

        finally:
            self.state_manager.clear_execution_id()

    async def _execute_node(
        self,
        execution_id: str,
        node: WorkflowNode,
        state: dict[str, Any],
        step_outputs: dict[str, ToolResult],
        query: str,
        user_id: int | None,
    ) -> dict[str, Any]:
        tool_candidates = [node.tool, *node.fallback_tools]
        last_error: str | None = None
        start = time.perf_counter()
        execution_log = WorkflowStepLog(
            step_id=node.id,
            tool=node.tool,
            dependencies=list(node.depends_on),
            input={},
            status="running",
        )

        self.tracer.start(execution_id, node.id, "tool", node.tool)
        self.state_manager.emit_event(
            SystemEvent(
                type=EventType.TOOL_EXECUTED,
                payload={
                    "stage": "node_start",
                    "step_id": node.id,
                    "tool": node.tool,
                    "depends_on": node.depends_on,
                },
                source="WorkflowExecutionEngine",
            ),
            execution_id=execution_id,
        )

        resolved_args = self._resolve_structure(copy.deepcopy(node.args), step_outputs, state)
        execution_log.input = resolved_args

        for candidate_index, candidate in enumerate(tool_candidates):
            tool = self.registry.get(candidate)
            if not tool:
                last_error = f"tool_not_found:{candidate}"
                continue

            if tool.permission_level == "restricted" and not self._is_allowed(tool.name, state):
                last_error = "permission_denied"
                continue

            params = dict(resolved_args)
            params["__force__"] = True
            context = ToolContext(
                user_id=user_id,
                query=query,
                state=state,
                params=params,
            )

            attempts = 0
            while attempts < 2:
                attempts += 1
                execution_log.attempts = attempts
                try:
                    result = await tool.execute(context)
                    if isinstance(result, ToolResult) and result.status == "error":
                        last_error = result.meta.get("error") or result.reason or "tool_error"
                        if attempts < 2:
                            await asyncio.sleep(0.15)
                            continue
                    else:
                        duration_ms = (time.perf_counter() - start) * 1000
                        execution_log.duration_ms = duration_ms
                        execution_log.status = "success" if not (isinstance(result, ToolResult) and result.status == "error") else "failed"
                        execution_log.output = result.to_dict() if isinstance(result, ToolResult) else result
                        execution_log.fallback_used = candidate if candidate != node.tool else None
                        if isinstance(result, ToolResult) and result.status == "error":
                            last_error = result.meta.get("error") or result.reason or "tool_error"
                        if isinstance(result, ToolResult) and result.status == "success":
                            self.tracer.end(execution_id, node.id, result=result.to_dict())
                        else:
                            self.tracer.end(execution_id, node.id, result=execution_log.output)

                        retrieved_file = self._extract_retrieved_file(candidate, result, resolved_args)
                        memory_context = self._extract_memory_context(candidate, result)
                        self._log_step(execution_id, node, resolved_args, result, duration_ms, candidate, attempts)
                        return {
                            "result": result,
                            "log": execution_log,
                            "retrieved_file": retrieved_file,
                            "memory_context": memory_context,
                        }
                except Exception as exc:
                    last_error = str(exc)
                    if attempts < 2:
                        await asyncio.sleep(0.15)
                        continue

            if candidate != node.tool:
                execution_log.fallback_used = candidate

        duration_ms = (time.perf_counter() - start) * 1000
        failure = ToolResult(
            tool=node.tool,
            output=None,
            status="error",
            confidence=0.0,
            relevance=0.0,
            meta={"error": last_error or "execution_failed"},
        )
        execution_log.duration_ms = duration_ms
        execution_log.status = "failed"
        execution_log.output = failure.to_dict()
        execution_log.error = last_error or "execution_failed"
        self.tracer.end(execution_id, node.id, error=execution_log.error)
        self._log_step(execution_id, node, resolved_args, failure, duration_ms, node.tool, attempts=2)
        return {
            "result": failure,
            "log": execution_log,
            "retrieved_file": None,
            "memory_context": None,
        }

    def _resolve_structure(self, value: Any, step_outputs: dict[str, ToolResult], state: dict[str, Any]) -> Any:
        if isinstance(value, dict):
            return {key: self._resolve_structure(item, step_outputs, state) for key, item in value.items()}
        if isinstance(value, list):
            return [self._resolve_structure(item, step_outputs, state) for item in value]
        if isinstance(value, str):
            return self._resolve_string(value, step_outputs, state)
        return value

    def _resolve_string(self, value: str, step_outputs: dict[str, ToolResult], state: dict[str, Any]) -> Any:
        match = re.fullmatch(r"\{\{\s*([^}]+?)\s*\}\}", value)
        if match:
            return self._resolve_reference(match.group(1), step_outputs, state)

        def replace_ref(match_obj: re.Match[str]) -> str:
            resolved = self._resolve_reference(match_obj.group(1), step_outputs, state)
            if isinstance(resolved, (dict, list)):
                return json.dumps(resolved, ensure_ascii=False)
            return "" if resolved is None else str(resolved)

        return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", replace_ref, value)

    def _resolve_reference(self, reference: str, step_outputs: dict[str, ToolResult], state: dict[str, Any]) -> Any:
        parts = [part.strip() for part in reference.split(".") if part.strip()]
        if not parts:
            return None

        if parts[0].startswith("step") and parts[0][4:].isdigit():
            step_id = parts[0]
            result = step_outputs.get(step_id)
            if result is None:
                return None
            target: Any = result.to_dict() if isinstance(result, ToolResult) else result
            for part in parts[1:]:
                if isinstance(target, dict):
                    if part == "result":
                        target = target.get("output", target)
                    else:
                        target = target.get(part)
                else:
                    target = getattr(target, part, None)
            return target

        if parts[0] == "state":
            target: Any = state
            for part in parts[1:]:
                if isinstance(target, dict):
                    target = target.get(part)
                else:
                    target = getattr(target, part, None)
            return target

        return None

    def _extract_retrieved_file(self, tool_name: str, result: ToolResult | Any, args: dict[str, Any]) -> str | None:
        payload = result.output if isinstance(result, ToolResult) else result
        if tool_name in {"read_file"} and isinstance(payload, dict):
            return payload.get("path")
        if tool_name in {"search_files", "file_search"} and isinstance(payload, dict):
            if payload.get("primary_path"):
                return payload.get("primary_path")
            matches = payload.get("matches") or []
            if matches:
                first = matches[0]
                if isinstance(first, dict):
                    return first.get("path") or first.get("display_path")
                if isinstance(first, str):
                    return first
        if isinstance(args, dict) and args.get("path"):
            return args.get("path")
        return None

    def _extract_memory_context(self, tool_name: str, result: ToolResult | Any) -> Any:
        payload = result.output if isinstance(result, ToolResult) else result
        if tool_name == "memory_search":
            return payload
        return None

    def _is_allowed(self, tool_name: str, state: dict[str, Any]) -> bool:
        permissions = state.get("permissions") or {}
        return bool(permissions.get(tool_name, False))

    def _build_memory_context(self, runtime_state: dict[str, Any]) -> str | None:
        memory_contexts = runtime_state.get("retrieved_context", {}).get("memory_search")
        if not memory_contexts:
            return None
        lines: list[str] = []
        for item in memory_contexts:
            if isinstance(item, dict):
                lines.append(json.dumps(item, ensure_ascii=False)[:800])
            else:
                lines.append(str(item)[:800])
        return "\n".join(lines)

    async def _generate_response(
        self,
        query: str,
        runtime_state: dict[str, Any],
        tool_results: list[ToolResult],
        memory_context: str | None,
        llm_model: str | None,
    ) -> str:
        compiler = ContextCompiler()
        prompt = compiler.compile(
            tools=tool_results,
            memory=memory_context,
            chat_history=runtime_state.get("history"),
            query=query,
            context_items=runtime_state.get("context_items"),
        )

        summary = runtime_state.get("summary") or {}
        execution_summary = json.dumps(summary, indent=2, ensure_ascii=False)
        full_prompt = (
            f"{prompt}\n\nExecution Summary:\n{execution_summary}\n\n"
            "Provide a concise answer grounded in the tool outputs. If information is incomplete, say so."
        )

        system_prompt = (
            "You are Cortex's response synthesizer. Use only the provided tool results and execution summary. "
            "Do not invent files, commands, or results. Be clear, concise, and accurate."
        )

        try:
            return await self.llm.generate(
                full_prompt,
                system_prompt=system_prompt,
                model=llm_model,
                api_key=runtime_state.get("api_key"),
                api_base_url=runtime_state.get("api_base_url"),
            )
        except Exception as exc:
            logger.warning("Workflow response generation failed, using fallback synthesis: %s", exc)
            if tool_results:
                return "\n\n".join(str(result) for result in tool_results if result is not None)
            return "No response could be generated."

    def _build_summary(
        self,
        graph: WorkflowGraph,
        runtime_state: dict[str, Any],
        tool_results: list[ToolResult],
        stop_reason: str | None,
    ) -> dict[str, Any]:
        retrieved_files = list(dict.fromkeys(runtime_state.get("retrieved_files", [])))
        tool_names = [result.tool for result in tool_results]
        steps = [
            {
                "step_id": log.step_id,
                "tool": log.tool,
                "dependencies": log.dependencies,
                "status": log.status,
                "duration_ms": round(log.duration_ms, 2),
                "fallback_used": log.fallback_used,
                "error": log.error,
            }
            for log in runtime_state.get("execution_logs", [])
        ]

        return {
            "goal": graph.plan.goal if graph.plan else "answer user request",
            "status": "failed" if runtime_state.get("errors") else "success",
            "stop_reason": stop_reason,
            "steps_executed": len(runtime_state.get("completed_steps", [])),
            "tools_used": tool_names,
            "retrieved_files": retrieved_files,
            "partial_results": bool(runtime_state.get("errors")),
            "execution_layers": graph.layers,
            "steps": steps,
        }

    def _log_step(
        self,
        execution_id: str,
        node: WorkflowNode,
        input_args: dict[str, Any],
        result: ToolResult | Any,
        duration_ms: float,
        tool_name: str,
        attempts: int,
    ) -> None:
        self.state_manager.emit_event(
            SystemEvent(
                type=EventType.TOOL_EXECUTED,
                payload={
                    "stage": "node_completed",
                    "execution_id": execution_id,
                    "step_id": node.id,
                    "tool": tool_name,
                    "attempts": attempts,
                    "duration_ms": round(duration_ms, 2),
                    "input": input_args,
                    "output_preview": self._preview(result),
                    "depends_on": node.depends_on,
                    "status": "success" if not (isinstance(result, ToolResult) and result.status == "error") else "failed",
                },
                source="WorkflowExecutionEngine",
            ),
            execution_id=execution_id,
        )

    def _preview(self, value: Any) -> Any:
        if isinstance(value, ToolResult):
            return {
                "tool": value.tool,
                "status": value.status,
                "output": self._preview(value.output),
                "meta": self._preview(value.meta),
            }
        if isinstance(value, dict):
            keys = list(value.keys())[:8]
            return {key: self._preview(value[key]) for key in keys}
        if isinstance(value, list):
            return [self._preview(item) for item in value[:5]]
        text = str(value)
        return text[:600] + ("..." if len(text) > 600 else "")
