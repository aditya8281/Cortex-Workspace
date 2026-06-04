import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.api.deps import get_db
from backend.app.intelligence.scope_config import SyncScopeConfig
from backend.app.intelligence.discovery import FilesystemDiscovery
from backend.app.ai.ingestion.scanner import RepoScanner
from backend.app.intelligence.sync_service import SyncService


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(tmp_path):
    db_file = tmp_path / "test_sync.db"
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
    # Setup test DB for FastAPI client overrides
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    db_file = tmp_path / "client_sync_test.db"
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


def test_scope_config_defaults_and_exclusions(tmp_path):
    # Patch config file path to tmp_path to isolate test config
    test_config_path = tmp_path / "sync_scope_config.json"
    with patch("backend.app.intelligence.scope_config.CONFIG_FILE", test_config_path):
        config = SyncScopeConfig()
        
        # Verify default includes contain active workspace and Home dir children if they exist
        assert len(config.include_folders) >= 1
        
        # Verify default system excludes are set
        assert len(config.exclude_folders) >= 2
        assert any("proc" in ex or "Windows" in ex or "System" in ex for ex in config.exclude_folders)

        # Test path exclusions matching system rules
        assert config.is_excluded("/proc/cpuinfo") is True
        assert config.is_excluded("/sys/kernel") is True
        
        # Test hidden files/directories exclusions
        assert config.is_excluded("/home/user/.git/config") is True
        assert config.is_excluded("/home/user/.cortex/index") is True
        
        # Test glob pattern exclusions
        assert config.is_excluded("/home/user/workspace/node_modules/express") is True
        assert config.is_excluded("/home/user/workspace/temp.tmp") is True

        # Test non-excluded standard paths
        assert config.is_excluded("/home/user/Documents/notes.txt") is False


def test_bfs_repo_scanner_prioritization(tmp_path):
    # Create mock folder structure
    include_dir = tmp_path / "include_dir"
    include_dir.mkdir()
    
    file_1 = include_dir / "index.py"
    file_1.write_text("print('hello')", encoding="utf-8")

    exclude_dir = include_dir / "node_modules"
    exclude_dir.mkdir()
    file_ignored = exclude_dir / "main.js"
    file_ignored.write_text("console.log('ignored')", encoding="utf-8")

    test_config_path = tmp_path / "sync_scope_config.json"
    with patch("backend.app.intelligence.scope_config.CONFIG_FILE", test_config_path):
        config = SyncScopeConfig()
        config.include_folders = [str(include_dir)]
        config.exclude_folders = [str(exclude_dir)]
        config.save()

        scanner = RepoScanner()
        files = scanner.scan()

        # Scanner must discover files in include_dir
        assert str(file_1.resolve()) in files
        # Scanner must skip excluded paths (node_modules)
        assert str(file_ignored.resolve()) not in files


def test_discovery_includes_standard_home_roots(tmp_path):
    home_dir = tmp_path / "home"
    documents = home_dir / "Documents"
    desktop = home_dir / "Desktop"
    downloads = home_dir / "Downloads"
    for folder in (documents, desktop, downloads):
        folder.mkdir(parents=True)

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    test_config_path = tmp_path / "sync_scope_config.json"
    with (
        patch("backend.app.intelligence.scope_config.CONFIG_FILE", test_config_path),
        patch("backend.app.intelligence.scope_config.Path.home", return_value=home_dir),
        patch("backend.app.intelligence.discovery.Path.home", return_value=home_dir),
        patch("backend.app.core.config.settings.WORKSPACE_ROOT", str(workspace)),
        patch("backend.app.intelligence.discovery.settings.WORKSPACE_ROOT", str(workspace)),
    ):
        discovery = FilesystemDiscovery()
        roots = {str(path) for path in discovery.discover_roots()}

    assert str(documents.resolve()) in roots
    assert str(desktop.resolve()) in roots
    assert str(downloads.resolve()) in roots
    assert str(workspace.resolve()) in roots


@pytest.mark.asyncio
async def test_sync_pause_resume_cancel(tmp_path):
    sync_service = SyncService()
    
    # Test pause
    sync_service.pause_sync()
    assert sync_service.progress_state.status == "paused"
    assert sync_service.progress_state.pause_event.is_set() is False

    # Test resume
    sync_service.resume_sync()
    assert sync_service.progress_state.status == "syncing"
    assert sync_service.progress_state.pause_event.is_set() is True

    # Test cancel
    sync_service.cancel_sync()
    assert sync_service.progress_state.status == "idle"
    assert sync_service.progress_state.cancel_event.is_set() is True


def test_incremental_sync_updates_progress_state(db_session, tmp_path):
    target = tmp_path / "notes.txt"
    target.write_text("hello cortex", encoding="utf-8")

    sync_service = SyncService()
    sync_service.scanner.scan_incremental = MagicMock(return_value=[str(target.resolve())])
    sync_service.indexing_service.incremental_update = AsyncMock(
        return_value=MagicMock(hash="abc123", metadata_json="{}")
    )
    sync_service.memory.count_entries = MagicMock(return_value=0)

    result = sync_service.run_incremental_sync(db_session, [str(target.resolve())])

    assert result["updated_files"] == 1
    assert sync_service.progress_state.status == "completed"
    assert sync_service.progress_state.indexed == 1
    assert sync_service.progress_state.total_files == 1
    assert sync_service.progress_state.current_path == "Incremental sync complete"


def test_incremental_sync_handles_deletions(db_session, tmp_path):
    missing = tmp_path / "deleted.txt"

    sync_service = SyncService()
    sync_service.indexing_service.incremental_update = AsyncMock(return_value=None)
    sync_service.scanner.scan_incremental = MagicMock(return_value=[])
    sync_service.memory.count_entries = MagicMock(return_value=0)

    result = sync_service.run_incremental_sync(db_session, [str(missing.resolve())])

    assert result["removed_files"] == 1
    assert sync_service.progress_state.indexed == 1


def test_api_scope_configurations(client, tmp_path):
    # Patch CONFIG_FILE for api endpoint test
    test_config_path = tmp_path / "sync_scope_config.json"
    with patch("backend.app.intelligence.scope_config.CONFIG_FILE", test_config_path):
        # 1. Get initial configuration
        response = client.get("/api/v1/sync/config")
        assert response.status_code == 200
        data = response.json()
        assert "include_folders" in data
        assert "exclude_folders" in data

        # 2. Add path to includes
        response = client.post("/api/v1/sync/config/include", json={"path": "/workspace/my-new-include"})
        assert response.status_code == 200
        data = response.json()
        assert "/workspace/my-new-include" in data["include_folders"]

        # 3. Add path to excludes
        response = client.post("/api/v1/sync/config/exclude", json={"path": "/workspace/my-new-include/logs"})
        assert response.status_code == 200
        data = response.json()
        assert "/workspace/my-new-include/logs" in data["exclude_folders"]

        # 4. Remove path from includes
        response = client.post("/api/v1/sync/config/include/remove", json={"path": "/workspace/my-new-include"})
        assert response.status_code == 200
        data = response.json()
        assert "/workspace/my-new-include" not in data["include_folders"]


def test_api_sync_controls(client):
    # 1. Test pause endpoint
    response = client.post("/api/v1/sync/pause")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 2. Test resume endpoint
    response = client.post("/api/v1/sync/resume")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 3. Test cancel endpoint
    response = client.post("/api/v1/sync/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
