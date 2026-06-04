import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.models.llm_model import CortexProvider, CortexModel
from backend.app.ai.model_registry import (
    ModelRegistry,
    store_key_securely,
    retrieve_key_securely
)

@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(tmp_path):
    db_file = tmp_path / "test.db"
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
    db_file = tmp_path / "client_test.db"
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

    test_app = FastAPI()
    test_app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    from backend.app.api.deps import get_db
    test_app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(test_app) as test_client:
            yield test_client
    finally:
        test_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()



def test_provider_key_secure_storage():
    provider_name = "MockOpenAI"
    key_val = "sk-test-key-12345"

    with patch("keyring.set_password") as mock_set, patch("keyring.get_password") as mock_get:
        mock_get.return_value = key_val
        
        # Test secure store using keyring
        encrypted_bytes = store_key_securely(provider_name, key_val)
        assert encrypted_bytes is None  # should save to keyring
        mock_set.assert_called_with("cortex-workspace", provider_name, key_val)

        # Test retrieve
        retrieved = retrieve_key_securely(provider_name, None)
        assert retrieved == key_val
        mock_get.assert_called_with("cortex-workspace", provider_name)


def test_provider_key_secure_storage_fallback():
    provider_name = "MockOpenAI-Fallback"
    key_val = "sk-fallback-key-12345"

    # Simulate keyring failing (e.g. headless environment)
    with patch("keyring.set_password", side_effect=Exception("Keyring failed")), \
         patch("keyring.get_password", return_value=None):
        
        # Test store (should fallback to DB encryption)
        encrypted_bytes = store_key_securely(provider_name, key_val)
        assert encrypted_bytes is not None  # Encrypted bytes saved
        
        # Test retrieve
        retrieved = retrieve_key_securely(provider_name, encrypted_bytes)
        assert retrieved == key_val


def test_seed_if_empty(db_session):
    ModelRegistry.seed_if_empty(db_session)
    
    # Check default providers exist
    providers = db_session.query(CortexProvider).all()
    assert len(providers) == 7
    provider_names = {p.name for p in providers}
    assert "OpenAI" in provider_names
    assert "Anthropic" in provider_names

    # Check default models exist
    models = db_session.query(CortexModel).all()
    assert len(models) == 10
    model_names = {m.name for m in models}
    assert "gpt-4o-mini" in model_names
    assert "claude-3-5-sonnet-latest" in model_names


@pytest.mark.asyncio
async def test_get_local_models():
    # Mock Ollama and LM Studio tags endpoints
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp_ollama = MagicMock()
        mock_resp_ollama.status_code = 200
        mock_resp_ollama.json.return_value = {
            "models": [
                {
                    "name": "llama3:8b",
                    "details": {
                        "parameter_size": "8B",
                        "quantization_level": "Q4_0"
                    }
                }
            ]
        }

        mock_resp_lm = MagicMock()
        mock_resp_lm.status_code = 200
        mock_resp_lm.json.return_value = {
            "data": [
                {"id": "meta-llama-3-8b-instruct"}
            ]
        }

        mock_get.side_effect = [mock_resp_ollama, mock_resp_lm]

        local_models = await ModelRegistry.get_local_models()
        assert len(local_models) == 2
        assert local_models[0]["name"] == "llama3:8b"
        assert local_models[0]["provider"] == "Ollama"
        assert local_models[1]["name"] == "meta-llama-3-8b-instruct"
        assert local_models[1]["provider"] == "LM Studio"


@pytest.mark.asyncio
async def test_validate_provider_success():
    with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
        # Mock models response
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            "data": [
                {"id": "gpt-4o-mini"}
            ]
        }
        mock_get.return_value = mock_get_resp

        # Mock completion response
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {
            "choices": [
                {
                    "message": {"content": "pong"}
                }
            ]
        }
        mock_post.return_value = mock_post_resp

        val_res = await ModelRegistry.validate_provider(
            name="OpenAI",
            base_url="https://api.openai.com/v1",
            api_key="sk-test"
        )
        
        assert val_res["valid"] is True
        assert "gpt-4o-mini" in val_res["models"]
        assert val_res["test_response"] == "pong"


def test_api_list_models_and_providers(client):
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    
    response_prov = client.get("/api/v1/models/providers")
    assert response_prov.status_code == 200
    data = response_prov.json()
    assert len(data) == 7
    assert data[0]["name"] == "OpenAI"


def test_api_validate_provider_endpoint(client):
    with patch("backend.app.ai.model_registry.ModelRegistry.validate_provider", new_callable=AsyncMock) as mock_val:
        mock_val.return_value = {"valid": True, "models": ["gpt-4o"], "test_response": "pong"}
        
        payload = {
            "name": "CustomOpenAI",
            "base_url": "http://localhost:8080/v1",
            "api_key": "custom-key"
        }
        response = client.post("/api/v1/models/providers/validate", json=payload)
        assert response.status_code == 200
        assert response.json()["valid"] is True


def test_provider_model_list_endpoint(client):
    with patch("backend.app.api.v1.models.ModelRegistry.validate_provider", new_callable=AsyncMock) as mock_val:
        mock_val.return_value = {
            "valid": True,
            "models": ["custom-a", "custom-b"],
            "default_model": "custom-a",
            "error": None,
        }
        create_response = client.post(
            "/api/v1/models/providers",
            json={
                "name": "CustomAI",
                "base_url": "http://localhost:8000/v1",
                "api_key": "secret",
                "is_enabled": True,
                "is_custom": True,
            },
        )
        assert create_response.status_code == 200

        response = client.get("/api/v1/models/providers/CustomAI/models")
        assert response.status_code == 200
        data = response.json()
        assert data["provider_name"] == "CustomAI"
        assert data["valid"] is True
        assert data["models"] == ["custom-a", "custom-b"]


def test_provider_default_update_and_delete(client):
    with patch("backend.app.api.v1.models.ModelRegistry.validate_provider", new_callable=AsyncMock) as mock_val:
        mock_val.return_value = {
            "valid": True,
            "models": ["custom-a"],
            "default_model": "custom-a",
            "error": None,
        }
        create_response = client.post(
            "/api/v1/models/providers",
            json={
                "name": "DisposableAI",
                "base_url": "http://localhost:9000/v1",
                "api_key": "secret",
                "is_enabled": True,
                "is_custom": True,
            },
        )
        assert create_response.status_code == 200

    update_response = client.put(
        "/api/v1/models/providers/DisposableAI/default-model",
        json={"default_model_name": "custom-a"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["default_model_name"] == "custom-a"

    delete_response = client.delete("/api/v1/models/providers/DisposableAI")
    assert delete_response.status_code == 200


def test_installed_and_check_endpoints_use_live_ollama(client):
    class FakeResponse:
        def __init__(self, payload):
            self.status_code = 200
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    with patch("backend.app.api.v1.models.httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = FakeResponse(
            {
                "models": [
                    {
                        "name": "llama3:8b",
                        "size": 123,
                        "details": {
                            "family": "llama",
                            "parameter_size": "8B",
                            "quantization_level": "Q4_0",
                        },
                    }
                ]
            }
        )
        installed_response = client.get("/api/v1/models/installed")
        assert installed_response.status_code == 200
        assert installed_response.json()[0]["name"] == "llama3:8b"

        check_response = client.get("/api/v1/models/check/llama3:8b")
        assert check_response.status_code == 200
        assert check_response.json()["installed"] is True


def test_api_select_model(client):
    with patch("backend.app.api.v1.models.ModelRegistry.list_models", new_callable=AsyncMock) as mock_models:
        mock_models.return_value = [
            {"name": "gpt-4o-mini", "id": "gpt-4o-mini", "provider": "OpenAI", "is_local": False}
        ]
        payload = {
            "model_name": "gpt-4o-mini"
        }
        response = client.post("/api/v1/models/select", json=payload)
        assert response.status_code == 200
        assert response.json()["selected_model"] == "gpt-4o-mini"


def test_api_select_model_auto(client):
    response = client.post("/api/v1/models/select", json={"model_name": "Auto", "session_id": "session-1"})
    assert response.status_code == 200
    data = response.json()
    assert data["selected_model"] == "Auto"
    assert data["resolved_model"] == "Auto"


def test_api_select_model_persists_session_state(client):
    with patch("backend.app.api.v1.models.ModelRegistry.list_models", new_callable=AsyncMock) as mock_models, \
         patch("backend.app.api.v1.models.redis_cache.ping", new_callable=AsyncMock) as mock_ping, \
         patch("backend.app.api.v1.models.redis_cache.set", new_callable=AsyncMock) as mock_set:
        mock_models.return_value = [
            {"name": "gpt-4o-mini", "id": "gpt-4o-mini", "provider": "OpenAI", "is_local": False}
        ]
        mock_ping.return_value = True
        response = client.post("/api/v1/models/select", json={"model_name": "gpt-4o-mini", "session_id": "session-2"})
        assert response.status_code == 200
        mock_ping.assert_awaited()
        mock_set.assert_awaited_once()
        assert "model_selection:session:session-2" in mock_set.await_args.args[0]


def test_api_routing_reads_are_public(client):
    response = client.get("/api/v1/models/routing/profiles")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    response = client.get("/api/v1/models/routing/routes")
    assert response.status_code == 200
    data = response.json()
    assert "profile_name" in data
    assert "routes" in data


def test_api_metrics_analytics_returns_200(client):
    response = client.get("/api/v1/models/metrics/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "routing_mode" in data
    assert "task_distribution" in data


@pytest.mark.asyncio
async def test_marketplace_uses_live_sources_only(client):
    with patch("backend.app.api.v1.models.ModelRegistry.get_dynamic_ollama_marketplace", new_callable=AsyncMock) as mock_registry, \
         patch("backend.app.api.v1.models.list_installed_models", new_callable=AsyncMock) as mock_installed:
        mock_registry.return_value = []
        mock_installed.return_value = []

        response = client.get("/api/v1/models/marketplace")
        assert response.status_code == 200
        assert response.json() == []
        mock_registry.assert_awaited()
        mock_installed.assert_awaited()


def test_model_download_job_routes(client):
    fake_job = {
        "id": "job-1",
        "model": "llama3:8b",
        "status": "queued",
        "percent": 0,
        "completed": 0,
        "total": 0,
        "message": "Queued for download",
        "error": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }

    with patch("backend.app.api.v1.models.model_download_manager.start_download", return_value=fake_job) as mock_start, \
         patch("backend.app.api.v1.models.model_download_manager.list_jobs", return_value=[fake_job]) as mock_list, \
         patch("backend.app.api.v1.models.model_download_manager.get_job", return_value=fake_job) as mock_get, \
         patch("backend.app.api.v1.models.model_download_manager.cancel_download", return_value={**fake_job, "status": "cancelled"}) as mock_cancel, \
         patch("backend.app.api.v1.models.model_download_manager.resume_download", return_value={**fake_job, "status": "queued"}) as mock_resume:
        response = client.post("/api/v1/models/pull", json={"model": "llama3:8b"})
        assert response.status_code == 200
        assert response.json()["id"] == "job-1"
        mock_start.assert_called_with("llama3:8b")

        response = client.get("/api/v1/models/downloads")
        assert response.status_code == 200
        assert response.json()[0]["id"] == "job-1"
        mock_list.assert_called()

        response = client.get("/api/v1/models/downloads/job-1")
        assert response.status_code == 200
        assert response.json()["id"] == "job-1"
        mock_get.assert_called_with("job-1")

        response = client.post("/api/v1/models/downloads/job-1/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
        mock_cancel.assert_called_with("job-1")

        response = client.post("/api/v1/models/downloads/job-1/resume")
        assert response.status_code == 200
        assert response.json()["status"] == "queued"
        mock_resume.assert_called_with("job-1")


def test_workspace_sync_route_exists(client):
    with patch("backend.app.api.v1.workspace.sync_service.run_full_sync", new_callable=AsyncMock) as mock_sync:
        response = client.post("/api/v1/workspace/sync")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["progress_message"] == "Queued workspace sync..."
