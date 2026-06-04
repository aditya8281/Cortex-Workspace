import pytest
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
# Import all models to ensure metadata is complete before creating tables
from backend.app.models.user import User
from backend.app.models.user_profile import UserProfile
from backend.app.models.user_settings import UserSettings
from backend.app.models.llm_model import (
    CortexProvider,
    CortexModel,
    CortexRoutingProfile,
    CortexTaskRoute,
    CortexModelMetric,
    CortexModelEvent
)
from backend.app.models.context_item import ContextItem as DBContextItem

from backend.app.agent.base import BaseAgent
from backend.app.agent.registry import AgentRegistry
from backend.app.agent.orchestrator import OrchestratorAgent, ContextBuilder
from backend.app.agent.agents import (
    ChatAgent,
    SearchAgent,
    RepositoryAgent,
    CodingAgent,
    PlanningAgent,
    MemoryAgent,
    ExecutionAgent,
    ResearchAgent
)
from backend.app.intelligence.models import (
    RepositoryProfile,
    KnowledgeEntry,
    PendingSystemAction,
    CortexAutomationSettings
)


class MockRouter:
    def __init__(self):
        self.last_prompt = None
        self.last_system_prompt = None

    async def route_and_generate(self, prompt, system_prompt, **kwargs):
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
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
    def __init__(self, workspace_root=None):
        self.workspace_root = workspace_root or Path("/mock/workspace")

    def search(self, query):
        return "MockFileSearchAgent: found file 'main.py'"


class MockSystemScanner:
    def scan(self, query):
        return "MockSystemScanner: CPU usage 15%, DB size 44KB"


class MockExecutor:
    def __init__(self, workspace_root=None):
        self.router = MockRouter()
        self.file_agent = MockFileSearchAgent(workspace_root)
        self.system_agent = MockSystemScanner()
        self.rag = self
        self.last_routing_info = None

    async def search(self, query, top_k=3):
        return [{"data": {"chunk": "Mock RAG chunk content"}}]


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(tmp_path):
    db_file = tmp_path / "test_framework.db"
    db_url = f"sqlite:///{db_file}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture(autouse=True)
def patch_db_session(db_session):
    import backend.app.db.session
    import backend.app.agent.agents
    import backend.app.agent.orchestrator

    original_db_session = backend.app.db.session.SessionLocal
    
    backend.app.db.session.SessionLocal = lambda: db_session
    backend.app.agent.agents.SessionLocal = lambda: db_session
    backend.app.agent.orchestrator.SessionLocal = lambda: db_session
    yield
    backend.app.db.session.SessionLocal = original_db_session
    backend.app.agent.agents.SessionLocal = original_db_session
    backend.app.agent.orchestrator.SessionLocal = original_db_session


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


@pytest.mark.asyncio
async def test_search_agent_integration(db_session):
    executor = MockExecutor()
    search_agent = SearchAgent(executor)
    
    # Pre-populate db memory/knowledge entry
    memory = KnowledgeEntry(
        category="document",
        title="Doc title",
        content="Interesting details about cortex search systems.",
        source_path="src/search.txt",
        source_key="doc:src/search.txt"
    )
    db_session.add(memory)
    db_session.commit()
    
    resp = await search_agent.execute("search cortex details", user_id=None)
    assert resp == "Response for query from model"
    
    last_prompt = executor.router.last_prompt
    assert "MockFileSearchAgent: found file 'main.py'" in last_prompt
    assert "Mock RAG chunk content" in last_prompt
    assert "Doc title: Interesting details about cortex search systems." in last_prompt


@pytest.mark.asyncio
async def test_repository_agent_integration(db_session):
    executor = MockExecutor()
    repo_agent = RepositoryAgent(executor)
    
    # Pre-populate RepositoryProfile
    profile = RepositoryProfile(
        path="/mock/workspace",
        name="test_repo",
        summary="A test repository profile",
        architecture_summary="A wonderful architecture overview.",
        tech_stack="Python, FastAPI, SQLite",
        dependencies_json='["sqlalchemy", "pytest"]',
        entry_points_json='["backend/app/main.py"]'
    )
    db_session.add(profile)
    db_session.commit()
    
    resp = await repo_agent.execute("explain architecture and tech stack")
    assert resp == "Response for query from model"
    
    last_prompt = executor.router.last_prompt
    assert "A wonderful architecture overview." in last_prompt
    assert "Python, FastAPI, SQLite" in last_prompt
    assert "test_repo" in last_prompt


@pytest.mark.asyncio
async def test_coding_agent_patch_generation():
    executor = MockExecutor()
    coding_agent = CodingAgent(executor)
    
    # Assert coding confidence triggers
    assert coding_agent.confidence("write a python function") > 0.8
    assert coding_agent.confidence("fix bug in executor.py") > 0.8
    
    resp = await coding_agent.execute("write a patch to add login function")
    assert resp == "Response for query from model"
    
    last_sys = executor.router.last_system_prompt
    assert "patch, diff, or file modification" in last_sys
    assert "```diff" in last_sys


@pytest.mark.asyncio
async def test_memory_agent_write_and_read(db_session):
    executor = MockExecutor()
    memory_agent = MemoryAgent(executor)
    
    # Test saving memory
    save_resp = await memory_agent.execute("remember that the codebase project is named Antigravity", user_id=42)
    assert "Memory saved successfully!" in save_resp
    assert "the codebase project is named Antigravity" in save_resp
    
    # Query database directly to verify persistence
    entries = db_session.query(KnowledgeEntry).filter(KnowledgeEntry.user_id == 42).all()
    assert len(entries) == 1
    assert entries[0].title == "Memory: the codebase project is named ..."
    assert entries[0].content == "the codebase project is named Antigravity"
    
    # Test querying/retrieval memory
    resp = await memory_agent.execute("what is the codebase project name?", user_id=42)
    assert resp == "Response for query from model"
    
    last_prompt = executor.router.last_prompt
    assert "Memory: the codebase project is named ..." in last_prompt


@pytest.mark.asyncio
async def test_planning_and_research_agents():
    executor = MockExecutor()
    
    planning_agent = PlanningAgent(executor)
    resp_plan = await planning_agent.execute("give me a roadmap for multi-agent framework")
    assert resp_plan == "Response for query from model"
    assert planning_agent.confidence("how to implement roadmap step-by-step") > 0.8
    
    research_agent = ResearchAgent(executor)
    resp_res = await research_agent.execute("deep dive explanation of RLHF")
    assert resp_res == "Response for query from model"
    assert research_agent.confidence("explain concept of pldnet") > 0.8


@pytest.mark.asyncio
async def test_execution_agent_permissions(db_session, tmp_path):
    executor = MockExecutor(workspace_root=tmp_path)
    exec_agent = ExecutionAgent(executor)
    
    # 1. Setup default approval automation settings
    settings = CortexAutomationSettings(
        user_id=101,
        automation_level="approval"
    )
    db_session.add(settings)
    db_session.commit()
    
    # Test run command blocked under "approval" level settings
    resp = await exec_agent.execute("run command make build", user_id=101)
    assert "Action Blocked (Approval Required)" in resp
    assert "run_command" in resp
    
    # Assert action was inserted into PendingSystemAction
    pending = db_session.query(PendingSystemAction).filter(PendingSystemAction.user_id == 101).first()
    assert pending is not None
    assert pending.action_type == "run_command"
    assert "make build" in pending.payload_json
    
    # 2. Test immediate read execution (read_file is exempt from approval check)
    dummy_file = tmp_path / "pyproject.toml"
    dummy_file.write_text("name = 'test-cortex'", encoding="utf-8")
    
    resp_read = await exec_agent.execute("read file pyproject.toml", user_id=101)
    assert "File Read Successfully" in resp_read
    assert "pyproject.toml" in resp_read
    assert "name = 'test-cortex'" in resp_read


@pytest.mark.asyncio
async def test_context_builder_caching(db_session):
    # Mock search so we can track calls
    search_mock = MagicMock()
    
    class TrackedExecutor(MockExecutor):
        async def search(self, query, top_k=3):
            search_mock(query)
            return [{"data": {"chunk": "Tracked search content"}}]

    executor = TrackedExecutor()
    builder = ContextBuilder(executor)
    
    # Build first time
    ctx1 = await builder.build(query="caching test query", user_id=55)
    assert search_mock.call_count == 1
    
    # Build second time with identical keys
    ctx2 = await builder.build(query="caching test query", user_id=55)
    assert search_mock.call_count == 1 # unchanged!
    assert ctx1 == ctx2
    
    # Build third time with different user
    ctx3 = await builder.build(query="caching test query", user_id=66)
    assert search_mock.call_count == 2
