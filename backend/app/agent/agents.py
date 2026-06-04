from typing import List, Dict, Any, Optional
import time
from backend.app.agent.base import BaseAgent
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

class ChatAgent(BaseAgent):
    name = "ChatAgent"
    description = "Handles conversational greetings, small talk, and general assistance."
    capabilities = ["chat"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower().strip()
        greetings = ["hello", "hi", "hey", "how are you", "who are you", "what is your name", "greetings", "good morning", "good afternoon"]
        if any(q.startswith(g) or f" {g} " in f" {q} " for g in greetings) or len(q.split()) <= 2:
            return 0.95
        return 0.15

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        system_prompt = (
            "You are a friendly, helpful, local-first AI assistant for Cortex Workspace.\n"
            "Respond directly to the user's greeting or general chat. Be warm, human-like, and conversational.\n"
            "Do not mention workspace directories, files, or tools unless the user explicitly asks about them."
        )
        prompt = f"{context or ''}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return res["response"]


class SearchAgent(BaseAgent):
    name = "SearchAgent"
    description = "Searches local workspace files and contents."
    capabilities = ["search", "file_search"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        search_keywords = ["find", "search", "locate", "where is", "look for", "grep", "file named", "pdf"]
        if any(kw in q for kw in search_keywords):
            return 0.90
        return 0.20

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        # Run filesystem file search
        search_results = self.executor.file_agent.search(query)
        system_prompt = (
            "You are a file search expert for Cortex Workspace.\n"
            "Answer the user's file query using the provided Search Results and Context.\n"
            "List matching files clearly and state if files cannot be found. Do not invent files."
        )
        prompt = f"{context or ''}\n\nSearch Results:\n{search_results}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return res["response"]


class RepoAnalysisAgent(BaseAgent):
    name = "RepoAnalysisAgent"
    description = "Analyzes repository structure, architecture summaries, and stack configuration."
    capabilities = ["repo_analysis"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        repo_keywords = ["architecture", "repo summary", "tech stack", "directory layout", "project structure", "workspace layout", "package.json", "pyproject.toml", "modules"]
        if any(kw in q for kw in repo_keywords):
            return 0.88
        return 0.25

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        system_prompt = (
            "You are a software architect analyzing the Cortex Workspace repository structure.\n"
            "Rely strictly on the provided Context (which includes repository profiles and structure summaries).\n"
            "Provide a clean, readable architectural explanation."
        )
        prompt = f"{context or ''}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return res["response"]


class CodingAgent(BaseAgent):
    name = "CodingAgent"
    description = "Writes, updates, parses, and explains code implementations."
    capabilities = ["coding"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        coding_keywords = ["code", "class", "function", "write a", "implement", "refactor", "bug", "fix", "syntax", "compile", "method", "python", "typescript", "javascript", "import", "class definition"]
        if any(kw in q for kw in coding_keywords):
            return 0.85
        return 0.30

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        system_prompt = (
            "You are an expert software developer.\n"
            "Your task is to write correct, clean, readable code and explain implementations.\n"
            "Use context code blocks if present. Follow design guidelines strictly."
        )
        prompt = f"{context or ''}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return res["response"]


class PlanningAgent(BaseAgent):
    name = "PlanningAgent"
    description = "Forms step-by-step implementation plans, roadmaps, and recipes."
    capabilities = ["planning"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        plan_keywords = ["plan", "steps", "how to", "roadmap", "recipe", "implementation steps", "strategy", "checklist"]
        if any(kw in q for kw in plan_keywords):
            return 0.87
        return 0.25

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        system_prompt = (
            "You are a software engineering planner.\n"
            "Break down the user's request into logical, structured, step-by-step engineering tasks.\n"
            "Keep the plan clear, actionable, and aligned with standard project layouts."
        )
        prompt = f"{context or ''}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return res["response"]


class MemoryRetrievalAgent(BaseAgent):
    name = "MemoryRetrievalAgent"
    description = "Recalls and retrieves stored persistent knowledge entries."
    capabilities = ["memory_retrieval"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        memory_keywords = ["memory", "recall", "stored", "learned", "note", "remember", "knowledge", "history"]
        if any(kw in q for kw in memory_keywords):
            return 0.88
        return 0.22

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        system_prompt = (
            "You are a memory recall agent for Cortex Workspace.\n"
            "Retrieve and summarize knowledge based on memory context, matching items accurately."
        )
        prompt = f"{context or ''}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return res["response"]


class ExecutionAgent(BaseAgent):
    name = "ExecutionAgent"
    description = "Performs system status diagnostic checks and executes commands."
    capabilities = ["execution"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        exec_keywords = ["run command", "execute command", "system status", "diagnostic", "health check", "scan health", "check port", "disk space", "cpu"]
        if any(kw in q for kw in exec_keywords):
            return 0.90
        return 0.20

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        diagnostics = self.executor.system_agent.scan(query)
        system_prompt = (
            "You are a system operations agent.\n"
            "Analyze system diagnostics and check health reports, providing direct troubleshooting answers."
        )
        prompt = f"{context or ''}\n\nSystem Diagnostics:\n{diagnostics}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return res["response"]


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    description = "Conducts deep concept research, investigation, and analysis."
    capabilities = ["research"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        research_keywords = ["research", "explain concept", "investigate", "deep dive", "theory", "paper", "pldnet", "rlhf"]
        if any(kw in q for kw in research_keywords):
            return 0.85
        return 0.35

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        system_prompt = (
            "You are a research agent.\n"
            "Synthesize deep insights from provided documentation, research concepts, and reference files."
        )
        prompt = f"{context or ''}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return res["response"]
