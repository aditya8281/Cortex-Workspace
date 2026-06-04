import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.api.deps import get_db
from backend.app.services.context_manager import ContextManager
from backend.app.schemas.context_item import ContextItem
from backend.app.executor.context_resolver import ContextResolver
from backend.app.intelligence.models import RepositoryProfile, KnowledgeEntry


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(tmp_path):
    db_file = tmp_path / "test_ctx.db"
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
    db_file = tmp_path / "client_ctx_test.db"
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


def test_context_manager_crud(db_session):
    manager = ContextManager(db_session)
    
    # 1. Attach context
    item = ContextItem(
        id="ctx-test-123",
        kind="file",
        title="test_file.py",
        path="backend/app/main.py",
        session_id="session-abc",
        content_preview="print('hello')"
    )
    db_item = manager.attach_context(item)
    assert db_item.id == "ctx-test-123"
    assert db_item.session_id == "session-abc"
    assert db_item.kind == "file"
    
    # 2. List context
    items = manager.list_context("session-abc")
    assert len(items) == 1
    assert items[0].title == "test_file.py"
    
    # 3. Update context
    updated = manager.update_context("ctx-test-123", {"title": "renamed_file.py"})
    assert updated is not None
    assert updated.title == "renamed_file.py"
    
    # 4. Resolve context
    resolved = manager.resolve_context(["ctx-test-123"])
    assert len(resolved) == 1
    assert resolved[0].title == "renamed_file.py"
    
    # 5. Remove context
    success = manager.remove_context("ctx-test-123")
    assert success is True
    assert len(manager.list_context("session-abc")) == 0


def test_context_api_endpoints(client):
    # 1. Attach context item
    payload = {
        "item": {
            "id": "ctx-api-test",
            "kind": "url",
            "title": "Cortex Docs",
            "url": "https://cortex.dev/docs",
            "session_id": "session-xyz"
        }
    }
    response = client.post("/api/v1/context/attach", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ctx-api-test"
    assert data["item"]["title"] == "Cortex Docs"

    # 2. List context items
    response = client.get("/api/v1/context/?session_id=session-xyz")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["id"] == "ctx-api-test"

    # 3. Patch context item
    patch_payload = {"title": "Updated Cortex Docs"}
    response = client.patch("/api/v1/context/ctx-api-test", json=patch_payload)
    assert response.status_code == 200
    assert response.json()["item"]["title"] == "Updated Cortex Docs"

    # 4. Resolve context items
    response = client.post("/api/v1/context/resolve", json=["ctx-api-test"])
    assert response.status_code == 200
    resolved = response.json()
    assert len(resolved) == 1
    assert resolved[0]["title"] == "Updated Cortex Docs"

    # 5. Delete context item
    response = client.delete("/api/v1/context/ctx-api-test")
    assert response.status_code == 200
    
    # 6. Verify deleted
    response = client.get("/api/v1/context/?session_id=session-xyz")
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_folder_context_resolver(tmp_path):
    # Setup dummy directory structure
    folder = tmp_path / "dummy_project"
    folder.mkdir()
    
    (folder / "README.md").write_text("# Dummy Project\nThis is a dummy project description.", encoding="utf-8")
    (folder / "pyproject.toml").write_text("[project]\nname = 'dummy'\ndependencies = []", encoding="utf-8")
    (folder / "main.py").write_text("def run():\n    print('run')", encoding="utf-8")
    
    src_dir = folder / "src"
    src_dir.mkdir()
    (src_dir / "utils.py").write_text("def helper():\n    pass", encoding="utf-8")
    
    item = {
        "id": "ctx-folder",
        "kind": "folder",
        "title": "dummy_project",
        "path": str(folder)
    }
    
    resolver = ContextResolver()
    resolved_item = await resolver._resolve_folder(item)
    
    content = resolved_item.get("resolved_content", "")
    assert "=== Folder Context ===" in content
    assert "Metadata:" in content
    assert "Total Files: 4" in content
    assert "Tech Stack: Python" in content
    assert "pyproject.toml" in content
    assert "README.md" in content
    assert "Folder Tree:" in content
    assert "dummy_project/" in content


@pytest.mark.asyncio
async def test_repo_context_resolver(db_session, tmp_path):
    # Setup dummy repository profile in database
    repo_dir = tmp_path / "dummy_repo"
    repo_dir.mkdir()
    
    profile = RepositoryProfile(
        path=str(repo_dir.resolve()),
        name="dummy_repo",
        summary="A test repository for context resolver",
        architecture_summary="Test split backend/frontend layout.",
        tech_stack="Python, TypeScript",
        dependencies_json=json.dumps(["fastapi", "pytest"]),
        important_files_json=json.dumps(["README.md", "pyproject.toml"])
    )
    db_session.add(profile)
    
    # Store repository memory/knowledge entry
    memory = KnowledgeEntry(
        category="repository",
        title="Repository: dummy_repo",
        content="Important design rationale: we use SQLite for simplicity.",
        source_path=str(repo_dir.resolve()),
        source_key=f"repo:{str(repo_dir.resolve())}"
    )
    db_session.add(memory)
    db_session.commit()

    item = {
        "id": "ctx-repo",
        "kind": "repo",
        "title": "dummy_repo",
        "path": str(repo_dir.resolve())
    }

    # Patch SessionLocal to return our test db_session in the resolver
    from backend.app.db import session
    original_session = session.SessionLocal
    session.SessionLocal = lambda: db_session

    try:
        resolver = ContextResolver()
        resolved_item = await resolver._resolve_repo(item)
        content = resolved_item.get("resolved_content", "")
        
        assert "=== Repository Context ===" in content
        assert "[Repository Memory]" in content
        assert "we use SQLite for simplicity" in content
        assert "dummy_repo" in content
        assert "fastapi" in content
        assert "pytest" in content
    finally:
        session.SessionLocal = original_session
