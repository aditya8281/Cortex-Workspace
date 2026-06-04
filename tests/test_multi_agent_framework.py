import pytest
import time
from typing import List, Dict, Any, Optional

from backend.app.agent.base import BaseAgent
from backend.app.agent.registry import AgentRegistry
from backend.app.agent.orchestrator import OrchestratorAgent, ContextBuilder
from backend.app.agent.agents import (
    ChatAgent,
    SearchAgent,
    RepoAnalysisAgent,
    CodingAgent,
    PlanningAgent,
    MemoryRetrievalAgent,
    ExecutionAgent,
    ResearchAgent
)


class MockRouter:
    async def route_and_generate(self, prompt, system_prompt, **kwargs):
        return {
            "response": "Response for query from model",
            "routing_info": {
                "model_used": "mock-llm-1.0",
                "provider": "MockProvider",
                "response_time": 0.05,
                "selection_reason": "Mocked test routing reasoning"
            }
        }


class MockFileSearchAgent:
    def search(self, query):
        return "MockFileSearchAgent: found file 'main.py'"


class MockSystemScanner:
    def scan(self, query):
        return "MockSystemScanner: CPU usage 15%, DB size 44KB"


class MockExecutor:
    def __init__(self):
        self.router = MockRouter()
        self.file_agent = MockFileSearchAgent()
        self.system_agent = MockSystemScanner()
        self.rag = self
        self.last_routing_info = None

    async def search(self, query, top_k=3):
        return [{"data": {"chunk": "Mock RAG chunk content"}}]


def test_agent_registry_routing():
    executor = MockExecutor()
    registry = AgentRegistry()
    
    chat_agent = ChatAgent(executor)
    coding_agent = CodingAgent(executor)
    
    registry.register(chat_agent)
    registry.register(coding_agent)
    
    assert len(registry.discover_agents()) == 2
    
    # 1. Routing chat query
    best_agent, score = registry.route_request("Hello Cortex! How are you today?")
    assert best_agent.name == "ChatAgent"
    assert score > 0.80

    # 2. Routing coding query
    best_agent, score = registry.route_request("write a python function to add two numbers")
    assert best_agent.name == "CodingAgent"
    assert score > 0.80


@pytest.mark.asyncio
async def test_subagents_execution():
    executor = MockExecutor()
    
    # 1. Chat agent execution
    chat_agent = ChatAgent(executor)
    resp = await chat_agent.execute("Hi there", context="Context info")
    assert resp == "Response for query from model"
    assert executor.last_routing_info["model_used"] == "mock-llm-1.0"
    
    # 2. Search agent execution
    search_agent = SearchAgent(executor)
    resp = await search_agent.execute("find main.py")
    assert resp == "Response for query from model"
    assert executor.last_routing_info["model_used"] == "mock-llm-1.0"


@pytest.mark.asyncio
async def test_orchestrator_execution():
    executor = MockExecutor()
    orchestrator = OrchestratorAgent(executor)
    
    # Check that task classification works
    task_chat = orchestrator.classify_task("hello, what is your name?")
    assert task_chat == "Chat"
    
    task_code = orchestrator.classify_task("write a loop in typescript")
    assert task_code == "Coding"

    task_search = orchestrator.classify_task("find files matching model")
    assert task_search == "Search"

    # Execute orchestrator routing
    response = await orchestrator.execute(
        query="implement a class in python to parse logs",
        history=[{"role": "user", "content": "Help me write code"}],
        user_id=1
    )
    
    assert response == "Response for query from model"
    assert orchestrator.last_trace["agent_selected"] == "CodingAgent"
    assert orchestrator.last_trace["classified_task"] == "Coding"
    assert orchestrator.last_trace["agent_confidence"] > 0.80
    assert orchestrator.last_trace["agent_execution_time"] > 0.0
