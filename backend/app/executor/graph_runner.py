import asyncio

from backend.app.executor.graph import ExecutionGraph, ExecutionStep
from backend.app.tools.base import ToolContext, ToolResult
from backend.app.executor.tool_intelligence import ToolIntelligence
from backend.app.executor.tool_fusion import ToolFusionEngine
from backend.app.executor.context_compiler import ContextCompiler

from backend.app.state.manager import StateManager
from backend.app.state.models import SystemEvent, EventType


class GraphRunner:
    def __init__(self, executor):
        self.executor = executor
        self.tools = self.executor.tool_registry
        self.tracer = self.executor.tracer
        self.state = self.executor.state

    async def run(
        self,
        graph: ExecutionGraph,
        query: str,
        user_id: int | None,
        intent=None,
        history=None,
        llm_model: str | None = None,
        embedding_model: str | None = None,
        vector_db: str | None = None,
        inference_engine: str | None = None,
        code_parsing: str | None = None,
        api_key: str | None = None,
        api_base_url: str | None = None
    ):

        state = {
            "execution_id": None,
            "query": query,
            "memory": None,
            "tools": [],
            "tool_map": {},
            "llm": None,
            "completed": set(),
            "execution_trace": [],
            "errors": [],
            "intent": intent,
            "history": history,
            "llm_model": llm_model,
            "embedding_model": embedding_model,
            "vector_db": vector_db,
            "inference_engine": inference_engine,
            "code_parsing": code_parsing,
            "api_key": api_key,
            "api_base_url": api_base_url,
        }

        execution_id = self.tracer.create_session()
        state["execution_id"] = execution_id

        pending_steps = graph.steps.copy()

        self.state.emit_event(SystemEvent(
            type=EventType.TOOL_EXECUTED,
            payload={
                "stage": "graph_execution_start",
                "execution_id": execution_id,
                "query": query,
                "steps": len(graph.steps)
            },
            source="GraphRunner"
        ), execution_id=execution_id)

        try:
            while pending_steps:
                ready_steps = [
                    s for s in pending_steps
                    if self._is_ready(s, state)
                ]

                if not ready_steps:
                    state["errors"].append({
                        "stage": "scheduler",
                        "error": "no_ready_steps",
                        "remaining_steps": [step.id for step in pending_steps],
                    })
                    break

                results = await asyncio.gather(
                    *[self._execute_step(execution_id, step, state, query, user_id) for step in ready_steps],
                    return_exceptions=True
                )

                for step, result in zip(ready_steps, results):
                    state["completed"].add(step.id)
                    state["tool_map"][step.id] = result
                    step.result = result

                    state["execution_trace"].append({
                        "step_id": step.id,
                        "type": step.type,
                        "name": step.name,
                        "depends_on": step.depends_on,
                        "result": self._preview(result)
                    })

                    if step.type == "memory":
                        state["memory"] = result

                    elif step.type == "tool":
                        tool_result = self._normalize_tool(result)
                        if tool_result:
                            state["tools"].append(tool_result)
                            if tool_result.status == "error":
                                state["errors"].append({
                                    "step_id": step.id,
                                    "tool": tool_result.tool,
                                    "error": tool_result.meta.get("error") or tool_result.meta.get("reason") or "tool_error",
                                })

                    elif step.type == "llm":
                        state["llm"] = result

                    if isinstance(result, ToolResult) and result.status == "error":
                        state["errors"].append({
                            "step_id": step.id,
                            "type": step.type,
                            "name": step.name,
                            "error": result.meta.get("error") or result.meta.get("reason") or "step_error",
                        })

                    pending_steps.remove(step)

            state["tools"] = ToolIntelligence().process(state["tools"])
            state["tools"] = ToolFusionEngine().process(state["tools"])

            status = "failed" if state["errors"] else "success"
            self.state.emit_event(SystemEvent(
                type=EventType.EXECUTION_COMPLETED,
                payload={
                    "execution_id": execution_id,
                    "query": query,
                    "tool_count": len(state["tools"]),
                    "steps_executed": len(state["execution_trace"]),
                    "status": status,
                    "error_count": len(state["errors"]),
                    "errors": state["errors"][:5],
                },
                source="GraphRunner"
            ), execution_id=execution_id)

            return state

        finally:
            self.state.clear_execution_id()

    def _is_ready(self, step: ExecutionStep, state) -> bool:
        return all(dep in state["completed"] for dep in step.depends_on)

    async def _execute_step(
        self,
        execution_id,
        step,
        state,
        query,
        user_id
    ):
        self.tracer.start(
            execution_id,
            step.id,
            step.type,
            step.name
        )

        try:
            self.state.emit_event(SystemEvent(
                type=EventType.TOOL_EXECUTED,
                payload={
                    "stage": "step_start",
                    "step_id": step.id,
                    "type": step.type,
                    "name": step.name
                },
                source="GraphRunner"
            ), execution_id=execution_id)

            if step.type == "memory":
                result = await self._run_memory(query, user_id)
            elif step.type == "tool":
                result = await self._run_tool(step.name, query, state, user_id)
            elif step.type == "llm":
                result = await self._run_llm(state, query, user_id)
            else:
                result = None

            self.tracer.end(
                execution_id,
                step.id,
                result=result
            )

            self.state.emit_event(SystemEvent(
                type=EventType.TOOL_EXECUTED,
                payload={
                    "stage": "step_completed",
                    "step_id": step.id,
                    "type": step.type,
                    "name": step.name,
                    "status": "success",
                    "result_preview": self._preview(result)
                },
                source="GraphRunner"
            ), execution_id=execution_id)

            return result

        except Exception as e:
            self.tracer.end(
                execution_id,
                step.id,
                error=str(e)
            )

            self.state.emit_event(SystemEvent(
                type=EventType.TOOL_EXECUTED,
                payload={
                    "execution_id": execution_id,
                    "step_id": step.id,
                    "stage": "step_failed",
                    "type": step.type,
                    "name": step.name,
                    "status": "failed",
                    "error": str(e)
                },
                source="GraphRunner"
            ), execution_id=execution_id)

            return ToolResult(
                tool=step.name or "unknown",
                output=None,
                confidence=0.0,
                relevance=0.0,
                status="error",
                meta={"error": str(e)}
            )

    async def _run_memory(self, query, user_id):
        from backend.app.db.session import SessionLocal
        from backend.app.intelligence.memory_service import PersistentMemoryService

        conversation_hits = None
        if user_id is not None:
            conversation_hits = self.executor.memory.search(user_id=user_id, query=query)

        knowledge_hits: list = []
        try:
            db = SessionLocal()
            try:
                knowledge_hits = PersistentMemoryService().search(
                    db, query, limit=6, user_id=user_id
                )
            finally:
                db.close()
        except Exception:
            knowledge_hits = []

        if conversation_hits:
            if knowledge_hits:
                knowledge_block = "\n".join(
                    f"- {item['title']}: {item['content'][:300]}" for item in knowledge_hits
                )
                return f"{conversation_hits}\n\n[Knowledge Memory]\n{knowledge_block}"
            return conversation_hits

        if knowledge_hits:
            knowledge_block = "\n".join(
                f"- {item['title']}: {item['content'][:300]}" for item in knowledge_hits
            )
            return f"[Knowledge Memory]\n{knowledge_block}"

        return None

    async def _run_tool(self, tool_name, query, state, user_id):
        tool = self.tools.get(tool_name)
        if not tool:
            return ToolResult(
                tool=tool_name,
                output=None,
                confidence=0.0,
                relevance=0.0,
                status="error",
                meta={"reason": "tool_not_found"}
            )

        context = ToolContext(
            user_id=user_id,
            query=query,
            state=state
        )

        return await self.tools.execute(tool_name, context)

    def _normalize_tool(self, result):
        if result is None:
            return None

        if isinstance(result, ToolResult):
            return result

        return ToolResult(
            tool="unknown",
            output=result,
            confidence=1.0,
            relevance=1.0,
            status="success",
            meta={"wrapped": True}
        )

    async def _run_llm(self, state, query, user_id=None):
        compiler = ContextCompiler()

        chat_history = None
        session_history = state.get("history")

        if session_history:
            chat_history = []
            for turn in session_history:
                role = getattr(turn, "role", None) or (turn.get("role") if isinstance(turn, dict) else None)
                content = getattr(turn, "content", None) or (turn.get("content") if isinstance(turn, dict) else None)
                if role and content:
                    chat_history.append({
                        "role": role,
                        "content": content
                    })
        
        if not chat_history and user_id is not None:
            try:
                db_history = self.executor.memory.get_recent_history(user_id)
                chat_history = []
                for turn in db_history:
                    chat_history.append({
                        "role": "user",
                        "content": turn["query"]
                    })
                    chat_history.append({
                        "role": "assistant",
                        "content": turn["response"]
                    })
            except Exception:
                pass

        prompt = compiler.compile(
            tools=state["tools"],
            memory=state["memory"],
            chat_history=chat_history,
            query=query
        )

        intent = state.get("intent")
        intent_type = intent.intent if intent else None

        if intent_type == "chat":
            system_prompt = (
                "You are a friendly, helpful, local-first AI assistant for Cortex Workspace.\n"
                "You should reply directly to the user's greeting, chat, question, or request using the context from the "
                "provided Recent Conversation History and Memory Context (if available).\n"
                "If the user is introducing themselves, greeting you, or having a general conversation, "
                "be warm, human-like, and conversational. Do NOT mention workspace directories, tools, or missing files "
                "unless they explicitly ask you about workspace files, code, or tools.\n"
                "Make sure to remember their name or details if they tell you."
            )
        else:
            system_prompt = (
                "You are a factual, local-first AI assistant for Cortex Workspace.\n"
                "You must base your answer strictly on the provided Tool Context, Memory Context, and Recent Conversation History.\n"
                "If the tools did not find any matching files, folders, or contents, you must clearly state that "
                "the files or directories do not exist in the workspace, and you must NOT invent or hallucinate any paths "
                "or directories that are not present in the tool results.\n"
                "Do not make up fake code, fake directories, or fake research papers."
            )

        return await self.executor.llm.generate(
            prompt,
            system_prompt=system_prompt,
            model=state.get("llm_model"),
            inference_engine=state.get("inference_engine"),
            api_key=state.get("api_key"),
            api_base_url=state.get("api_base_url")
        )

    def _preview(self, value):
        if value is None:
            return None

        if isinstance(value, ToolResult):
            return {
                "tool": value.tool,
                "status": value.status,
                "confidence": value.confidence,
                "relevance": value.relevance,
                "output": self._preview(value.output),
            }

        if isinstance(value, dict):
            preview = {}
            for key in list(value.keys())[:6]:
                preview[key] = self._preview(value[key])
            return preview

        if isinstance(value, list):
            return [self._preview(item) for item in value[:5]]

        text = str(value)
        return text[:500]
