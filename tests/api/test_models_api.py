from unittest.mock import AsyncMock, MagicMock, patch

HEADERS = {"Authorization": "Bearer fake-token"}


def test_list_models(client, mock_auth):
    with (
        patch(
            "backend.app.services.intelligence.ollama_catalog.get_ollama_catalog",
            new_callable=AsyncMock,
            return_value=([], MagicMock()),
        ),
        patch("backend.app.api.v1.developer.catalog.llm_manager") as mock_llm,
    ):
        mock_llm.list_all_models = AsyncMock(return_value=[])
        resp = client.get("/api/v1/models", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "total_count" in data
        assert "downloaded_count" in data
        assert "available_from_providers" in data


def test_recommended_models(client, mock_auth):
    mock_hw = MagicMock()
    mock_hw.to_dict.return_value = {"ram_gb": 16, "gpu_name": None}

    mock_rec = MagicMock()
    mock_rec.score = 80.0
    mock_rec.performance = MagicMock()
    mock_rec.performance.tokens_per_second = 30.0
    mock_rec.performance.prompt_eval_tps = 50.0
    mock_rec.performance.memory_usage_gb = 4.0
    mock_rec.performance.vram_usage_gb = 0.0
    mock_rec.performance.quantization_quality = "good"
    mock_rec.performance.quality_notes = "ok"
    mock_rec.performance.speed_rating = "fast"
    mock_rec.performance.fit_rating = "good"
    mock_rec.performance.context_length_max = 128000
    mock_rec.variant = MagicMock()
    mock_rec.variant.quantization = "Q4_K_M"
    mock_rec.variant.size_gb = 4.5
    mock_rec.variant.vram_required_gb = 5.0
    mock_rec.variant.quality_score = 90.0
    mock_rec.catalog_entry = MagicMock()
    mock_rec.catalog_entry.model_id = "test-model"
    mock_rec.catalog_entry.display_name = "Test Model"
    mock_rec.catalog_entry.family = "test"
    mock_rec.catalog_entry.parameter_count = 8.0
    mock_rec.catalog_entry.capabilities = ["chat"]
    mock_rec.catalog_entry.description = "A test model"
    mock_rec.why_recommended = "Good fit"
    mock_rec.quality_tradeoff = "None"
    mock_rec.hardware_suitability = "Excellent"

    mock_engine = MagicMock()
    mock_engine.recommend_all.return_value = {
        "coding": [mock_rec],
    }

    with (
        patch("backend.app.api.v1.developer.catalog._detect_hardware_full", return_value=mock_hw),
        patch("backend.app.services.awareness.hardware.detect_hardware", return_value=mock_hw),
        patch("backend.app.services.intelligence.recommendation.RecommendationEngine", return_value=mock_engine),
        patch("backend.app.services.intelligence.model_catalog.CatalogueManager") as mock_cat_mgr,
    ):
        mock_cat_mgr.return_value.get_all_catalogue.return_value = []
        resp = client.get("/api/v1/models/recommended", headers=HEADERS)
        assert resp.status_code == 200


def test_hardware_info(client, mock_auth):
    mock_profile = MagicMock()
    mock_profile.to_dict.return_value = {
        "ram_gb": 16.0,
        "ram_available_gb": 8.0,
        "ram_percent": 50.0,
        "cpu_count": 8,
        "cpu_threads": 16,
        "cpu_freq_mhz": 3600.0,
        "cpu_arch": "x86_64",
        "gpu": {"available": True, "name": "RTX 3060", "type": "nvidia", "vram_gb": 12.0, "vram_available_gb": 10.0},
        "disk_free_gb": 100.0,
        "supports_cuda": True,
        "supports_metal": False,
    }
    with patch("backend.app.api.v1.developer.catalog._detect_hardware_full", return_value=mock_profile):
        resp = client.get("/api/v1/models/hardware", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "ram_gb" in data
        assert data["ram_gb"] == 16.0


def test_model_health(client, mock_auth):
    with patch("backend.app.api.v1.system.llm_health.llm_manager") as mock_llm:
        mock_llm.health_check = AsyncMock(return_value={"ollama": {"available": True}})
        resp = client.get("/api/v1/models/health", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "latency_ms" in data


def test_model_metrics(client, mock_auth):
    with patch("backend.app.api.v1.system.llm_health.llm_manager") as mock_llm:
        mock_llm.get_metrics.return_value = {
            "total_prompt_tokens": 700,
            "total_completion_tokens": 300,
            "total_requests": 5,
        }
        resp = client.get("/api/v1/models/metrics", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_tokens"] == 1000
        assert data["total_requests"] == 5


def test_model_storage(client, mock_auth):
    mock_disk = MagicMock()
    mock_disk.total = 500 * 1024**3
    mock_disk.used = 200 * 1024**3
    mock_disk.free = 300 * 1024**3

    mock_path = MagicMock()
    mock_path.exists.return_value = False

    with (
        patch("backend.app.api.v1.privacy.settings.psutil") as mock_psutil,
        patch("backend.app.api.v1.privacy.settings.Path", return_value=mock_path),
    ):
        mock_psutil.disk_usage.return_value = mock_disk
        resp = client.get("/api/v1/privacy/models/storage", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_disk_gb" in data
        assert "free_disk_gb" in data
        assert "models_total_gb" in data


def test_model_autocomplete(client, mock_auth):
    mock_service = MagicMock()
    mock_service.autocomplete.return_value = ["llama-3.1-8b", "llama-3.2-3b"]

    with patch("backend.app.api.v1.developer.catalog.ModelSearchService", return_value=mock_service):
        resp = client.get("/api/v1/models/autocomplete?q=llama", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["suggestions"] == ["llama-3.1-8b", "llama-3.2-3b"]


def test_model_search(client, mock_auth):
    mock_model = MagicMock()
    mock_model.model_id = "llama-3.1-8b-instruct"
    mock_model.display_name = "Llama 3.1 8B"
    mock_model.family = "llama"
    mock_model.provider = "ollama"
    mock_model.parameter_count = 8.0
    mock_model.architecture = "transformer"
    mock_model.context_length_default = 128000
    mock_model.capabilities = ["chat"]
    mock_model.description = "A model"
    mock_model.tags = ["popular"]

    mock_service = MagicMock()
    mock_service.search.return_value = [mock_model]

    with patch("backend.app.api.v1.developer.catalog.ModelSearchService", return_value=mock_service):
        resp = client.get("/api/v1/models/search?q=llama", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 1
        assert data["models"][0]["model_id"] == "llama-3.1-8b-instruct"


def test_model_installed(client, mock_auth):
    mock_catalogue = MagicMock()
    mock_catalogue.get_all_catalogue.return_value = []

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"models": []}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_db = MagicMock()

    def _mock_get_db():
        yield mock_db

    with (
        patch("backend.app.services.intelligence.model_catalog.CatalogueManager", return_value=mock_catalogue),
        patch("backend.app.core.db.get_db", _mock_get_db),
        patch("httpx.AsyncClient", return_value=mock_client),
    ):
        resp = client.get("/api/v1/models/installed", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "installed_count" in data


def test_model_detail_not_found(client, mock_auth):
    with patch("backend.app.api.v1.developer.catalog.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__next__ = MagicMock(return_value=mock_db)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        resp = client.get("/api/v1/models/nonexistent-model", headers=HEADERS)
        assert resp.status_code == 404
