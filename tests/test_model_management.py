import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
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

    from backend.app.api.deps import get_db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
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


def test_api_select_model(client):
    payload = {
        "model_name": "gpt-4o-mini"
    }
    response = client.post("/api/v1/models/select", json=payload)
    assert response.status_code == 200
    assert response.json()["selected_model"] == "gpt-4o-mini"
