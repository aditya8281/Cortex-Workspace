import pytest
import numpy as np
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.api.deps import get_db
from backend.app.models.hierarchical_memory import HierarchicalNode
from backend.app.services.hierarchical_rag import HierarchicalRAGService
from backend.app.agent.orchestrator import ContextBuilder


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(tmp_path):
    db_file = tmp_path / "test_rag.db"
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


@pytest.fixture(name="client", scope="function")
def fixture_client(tmp_path):
    db_file = tmp_path / "client_rag_test.db"
    db_url = f"sqlite:///{db_file}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_query_classification():
    rag_service = HierarchicalRAGService()

    # Fast path examples (metadata/names)
    assert rag_service.classify_query("where is orchestrator.py?") == "fast"
    assert rag_service.classify_query("find file main.py") == "fast"
    assert rag_service.classify_query("pyproject.toml") == "fast"
    assert rag_service.classify_query("show path of setup.cfg") == "fast"

    # Deep path examples (conceptual/explanation)
    assert rag_service.classify_query("explain how the multi-agent orchestration works") == "deep"
    assert rag_service.classify_query("what are the benefits of caching?") == "deep"
    assert rag_service.classify_query("how does the vector search retrieve relevant nodes?") == "deep"


@pytest.mark.asyncio
async def test_search_fast_path(db_session):
    # Setup node database entries
    repo_node = HierarchicalNode(
        node_type="repo",
        path="/workspace/myrepo",
        content="Test repository summary",
        parent_id=None
    )
    db_session.add(repo_node)
    db_session.commit()

    file_node = HierarchicalNode(
        node_type="file",
        path="/workspace/myrepo/main.py",
        content="Main entrypoint module",
        parent_id=repo_node.id
    )
    db_session.add(file_node)

    chunk_node = HierarchicalNode(
        node_type="chunk",
        path="",
        content="def start_app():\n    print('cortex is running')",
        parent_id=file_node.id
    )
    db_session.add(chunk_node)
    db_session.commit()

    rag_service = HierarchicalRAGService()

    # Match filename directly
    results = await rag_service.search("main.py", db_session, mode="fast")
    assert len(results) >= 1
    assert results[0]["node_type"] == "file"
    assert "main.py" in results[0]["file_path"]

    # Match text substring
    results_chunk = await rag_service.search("cortex is running", db_session, mode="fast")
    assert len(results_chunk) >= 1
    assert results_chunk[0]["node_type"] == "chunk"
    assert "cortex is running" in results_chunk[0]["text"]


@pytest.mark.asyncio
async def test_search_deep_path(db_session):
    repo_node = HierarchicalNode(
        node_type="repo",
        path="/workspace/myrepo",
        content="Test repository summary",
        parent_id=None
    )
    db_session.add(repo_node)
    db_session.commit()

    file_node = HierarchicalNode(
        node_type="file",
        path="/workspace/myrepo/app.py",
        content="Application core script",
        parent_id=repo_node.id
    )
    db_session.add(file_node)

    chunk_node = HierarchicalNode(
        node_type="chunk",
        path="",
        content="class ApplicationEngine:\n    def start(self):\n        pass",
        parent_id=file_node.id
    )
    db_session.add(chunk_node)
    db_session.commit()

    rag_service = HierarchicalRAGService()

    # Mock SentenceTransformer embedder encode method
    mock_embedder = MagicMock()
    mock_embedder.encode.side_effect = lambda texts: np.random.rand(len(texts), 384).astype("float32")
    rag_service.indexing_service._embedder = mock_embedder

    # Mock the indexing search call
    with patch.object(rag_service.indexing_service, "search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [
            {
                "id": chunk_node.id,
                "text": chunk_node.content,
                "file_path": "/workspace/myrepo/app.py",
                "score": 0.85,
                "metadata": {}
            }
        ]

        results = await rag_service.search("how does the application engine start", db_session, mode="deep")
        assert len(results) >= 1
        # The result must include the chunk itself, plus any graph expansions (such as siblings/imports)
        assert any(r["id"] == chunk_node.id for r in results)
        assert results[0]["node_type"] == "chunk"
        assert "ApplicationEngine" in results[0]["text"]


@pytest.mark.asyncio
async def test_resolve_imports(db_session):
    repo_node = HierarchicalNode(
        node_type="repo",
        path="/workspace/myrepo",
        content="Test repository summary",
        parent_id=None
    )
    db_session.add(repo_node)
    db_session.commit()

    target_file = HierarchicalNode(
        node_type="file",
        path="/workspace/myrepo/utils.py",
        content="Utility library module",
        parent_id=repo_node.id
    )
    db_session.add(target_file)
    db_session.commit()

    rag_service = HierarchicalRAGService()

    # Python import parsing test
    chunk_text_py = "from myrepo.utils import helper_func\nhelper_func()"
    resolved = rag_service._resolve_imports(chunk_text_py, "/workspace/myrepo/main.py", db_session)
    assert len(resolved) >= 1
    assert resolved[0].id == target_file.id

    # JS/TS import parsing test
    chunk_text_js = "import { utils } from './utils'\nconsole.log(utils);"
    resolved_js = rag_service._resolve_imports(chunk_text_js, "/workspace/myrepo/main.py", db_session)
    assert len(resolved_js) >= 1
    assert resolved_js[0].id == target_file.id


@pytest.mark.asyncio
async def test_graph_expansion(db_session):
    repo_node = HierarchicalNode(
        node_type="repo",
        path="/workspace/myrepo",
        content="Test repository summary",
        parent_id=None
    )
    db_session.add(repo_node)
    db_session.commit()

    folder_node = HierarchicalNode(
        node_type="folder",
        path="/workspace/myrepo/src",
        content="Source directory",
        parent_id=repo_node.id
    )
    db_session.add(folder_node)
    db_session.commit()

    file_node_1 = HierarchicalNode(
        node_type="file",
        path="/workspace/myrepo/src/main.py",
        content="Main file",
        parent_id=folder_node.id
    )
    file_node_2 = HierarchicalNode(
        node_type="file",
        path="/workspace/myrepo/src/helper.py",
        content="Helper file",
        parent_id=folder_node.id
    )
    db_session.add(file_node_1)
    db_session.add(file_node_2)
    db_session.commit()

    chunk_node = HierarchicalNode(
        node_type="chunk",
        path="",
        content="import helper\ndef run():\n    pass",
        parent_id=file_node_1.id
    )
    db_session.add(chunk_node)
    db_session.commit()

    rag_service = HierarchicalRAGService()

    # 1. Expand chunk node -> fetches sibling files and module imports
    assoc_chunk = rag_service.expand_graph(chunk_node.id, db_session)
    assert len(assoc_chunk) >= 1
    # Sibling file: src/helper.py should be fetched
    assert any(a["node_type"] == "file" and "helper.py" in a["file_path"] for a in assoc_chunk)

    # 2. Expand file node -> fetches parent folder summary
    assoc_file = rag_service.expand_graph(file_node_1.id, db_session)
    assert len(assoc_file) >= 1
    assert assoc_file[0]["node_type"] == "folder"
    assert "Source directory" in assoc_file[0]["text"]


@pytest.mark.asyncio
async def test_build_context_and_compression(db_session):
    repo_node = HierarchicalNode(
        node_type="repo",
        path="/workspace/myrepo",
        content="Test repository summary",
        metadata_json=json.dumps({
            "structure_summary": "Clean multi-tier layout.",
            "important_files": ["README.md", "src/main.py"]
        }),
        parent_id=None
    )
    db_session.add(repo_node)
    db_session.commit()

    rag_service = HierarchicalRAGService()

    # Mock embedder and ranker to avoid loading actualSentenceTransformer
    mock_embedder = MagicMock()
    mock_embedder.encode.side_effect = lambda texts: np.random.rand(len(texts), 384).astype("float32")
    rag_service.indexing_service._embedder = mock_embedder

    with patch.object(rag_service, "search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [
            {
                "id": 999,
                "node_type": "chunk",
                "text": "This is a relevant chunk text matching queries.",
                "file_path": "/workspace/myrepo/src/main.py",
                "score": 0.9,
                "metadata": {}
            }
        ]

        # 1. Test normal context compilation
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"}
        ]
        context = await rag_service.build_context(
            query="caching",
            db=db_session,
            history=history
        )
        assert "Repository Context" in context
        assert "Conversation History" in context
        assert "Retrieval Context" in context
        assert "This is a relevant chunk text" in context

        # 2. Test context compression (input exceeds 8000 characters)
        large_history = [{"role": "user", "content": "a" * 1500} for _ in range(10)]
        compressed_context = await rag_service.build_context(
            query="caching",
            db=db_session,
            history=large_history
        )
        assert len(compressed_context) < 8000
        assert "Repository Context (Compressed)" in compressed_context
        assert "Conversation History (Compressed)" in compressed_context
        assert "Retrieval Context (Compressed RAG)" in compressed_context


@pytest.mark.asyncio
async def test_api_endpoints(client, db_session):
    # Setup node in DB used by client override db
    repo_node = HierarchicalNode(
        node_type="repo",
        path="/workspace/testproject",
        content="Endpoint project summary",
        parent_id=None
    )
    db_session.add(repo_node)
    db_session.commit()

    file_node = HierarchicalNode(
        node_type="file",
        path="/workspace/testproject/api.py",
        content="FastAPI service endpoints",
        parent_id=repo_node.id
    )
    db_session.add(file_node)
    db_session.commit()

    chunk_node = HierarchicalNode(
        node_type="chunk",
        path="",
        content="app = FastAPI()",
        parent_id=file_node.id
    )
    db_session.add(chunk_node)
    db_session.commit()

    # 1. Test retrieve_context endpoint
    response = client.get("/api/v1/sync/hierarchical/retrieve_context?query=FastAPI")
    assert response.status_code == 200
    data = response.json()
    assert "context" in data

    # 2. Test expand_graph endpoint
    response = client.get(f"/api/v1/sync/hierarchical/expand_graph?node_id={file_node.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["node_id"] == file_node.id
    assert "associations" in data

    # 3. Test build_context endpoint
    payload = {
        "query": "FastAPI",
        "history": [{"role": "user", "content": "hi"}],
        "user_id": 42
    }
    response = client.post("/api/v1/sync/hierarchical/build_context", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "context" in data
