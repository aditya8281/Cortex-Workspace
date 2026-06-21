"""Tests for HuggingFace provider adapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.app.services.providers.huggingface import HuggingFaceProvider


@pytest.fixture
def provider():
    return HuggingFaceProvider(token=None, base_url="https://huggingface.co/api")


@pytest.fixture
def authed_provider():
    return HuggingFaceProvider(token="hf_test_token", base_url="https://huggingface.co/api")


def _make_response(json_data=None, status_code=200, headers=None, text=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=json_data)
    resp.headers = headers or {}
    resp.text = text or ""
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=resp)
    return resp


def test_provider_name(provider):
    assert provider.name == "huggingface"
    assert provider.display_name == "HuggingFace"


def test_provider_name_authed(authed_provider):
    assert authed_provider.name == "huggingface"
    assert "Authorization" in authed_provider._client.headers


@pytest.mark.asyncio
async def test_health_check_success(provider):
    resp = _make_response(json_data=[{"id": "test"}])
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_health_check_failure(provider):
    with patch.object(provider._client, "get", side_effect=Exception("Connection refused")):
        assert await provider.health_check() is False


@pytest.mark.asyncio
async def test_list_models_empty(provider):
    resp = _make_response(json_data=[])
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        models = await provider.list_models()
        assert models == []


@pytest.mark.asyncio
async def test_list_models_with_gguf_data(provider):
    hf_data = [
        {
            "modelId": "TheBloke/Llama-2-7B-GGUF",
            "id": "TheBloke/Llama-2-7B-GGUF",
            "tags": ["llama", "gguf", "7b-parameter", "text-generation"],
            "pipeline_tag": "text-generation",
            "downloads": 50000,
            "likes": 100,
            "license": "llama2",
            "description": "GGUF quantized Llama 2 7B",
        },
        {
            "modelId": "bartowski/Mistral-7B-v0.1-GGUF",
            "id": "bartowski/Mistral-7B-v0.1-GGUF",
            "tags": ["mistral", "gguf", "7b-parameter"],
            "pipeline_tag": "text-generation",
            "downloads": 30000,
            "likes": 80,
        },
    ]
    resp = _make_response(json_data=hf_data, headers={"link": ""})
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        models = await provider.list_models()
        assert len(models) == 2
        assert models[0].provider_model_id == "TheBloke/Llama-2-7B-GGUF"
        assert models[0].display_name == "Llama-2-7B-GGUF"
        assert models[0].family == "llama"
        assert "gguf" in models[0].capabilities
        assert "chat" in models[0].capabilities
        assert models[0].parameter_count == 7.0
        assert models[0].license == "llama2"
        assert models[0].source_url == "https://huggingface.co/TheBloke/Llama-2-7B-GGUF"
        assert models[1].provider_model_id == "bartowski/Mistral-7B-v0.1-GGUF"
        assert models[1].family == "mistral"


@pytest.mark.asyncio
async def test_list_models_pagination(provider):
    page1 = [{"modelId": "org/model-a", "tags": ["gguf"], "pipeline_tag": "text-generation"}]
    page2 = [{"modelId": "org/model-b", "tags": ["gguf"], "pipeline_tag": "text-generation"}]

    resp1 = _make_response(
        json_data=page1, headers={"link": '<https://huggingface.co/api/models?cursor=abc>; rel="next"'}
    )
    resp2 = _make_response(json_data=page2, headers={""})

    call_count = 0

    async def mock_get(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return resp1
        return resp2

    with patch.object(provider._client, "get", side_effect=mock_get):
        models = await provider.list_models()
        assert len(models) == 2
        assert models[0].provider_model_id == "org/model-a"
        assert models[1].provider_model_id == "org/model-b"


@pytest.mark.asyncio
async def test_list_models_failure(provider):
    with patch.object(provider._client, "get", side_effect=Exception("timeout")):
        models = await provider.list_models()
        assert models == []


@pytest.mark.asyncio
async def test_get_model_variants(provider):
    files_data = [
        {"path": "model-Q4_K_M.gguf", "size": 4_000_000_000},
        {"path": "model-Q8_0.gguf", "size": 7_000_000_000},
        {"path": "model-F16.gguf", "size": 14_000_000_000},
        {"path": "README.md", "size": 1000},
    ]
    resp = _make_response(json_data=files_data)
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        variants = await provider.get_model_variants("TheBloke/llama-7B-GGUF")
        assert len(variants) == 3
        assert variants[0].quantization == "Q4_K_M"
        assert variants[0].size_bytes == 4_000_000_000
        assert variants[0].size_gb == 3.73
        assert variants[0].download_url is not None
        assert variants[1].quantization == "Q8_0"
        assert variants[2].quantization == "F16"


@pytest.mark.asyncio
async def test_get_model_variants_no_gguf(provider):
    files_data = [{"path": "model.safetensors", "size": 1000}]
    resp = _make_response(json_data=files_data)
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        variants = await provider.get_model_variants("org/model")
        assert variants == []


@pytest.mark.asyncio
async def test_get_model_variants_failure(provider):
    with patch.object(provider._client, "get", side_effect=Exception("not found")):
        variants = await provider.get_model_variants("nonexistent")
        assert variants == []


@pytest.mark.asyncio
async def test_get_model_detail(provider):
    detail_data = {
        "modelId": "meta-llama/Llama-2-7b-hf",
        "id": "meta-llama/Llama-2-7b-hf",
        "tags": ["llama", "text-generation", "pytorch", "transformers"],
        "pipeline_tag": "text-generation",
        "downloads": 100000,
        "likes": 200,
        "license": "llama2",
        "description": "Llama 2 7B model",
        "safetensors": {"total": 7_000_000_000},
    }
    resp = _make_response(json_data=detail_data)
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        detail = await provider.get_model_detail("meta-llama/Llama-2-7b-hf")
        assert detail is not None
        assert detail.provider_model_id == "meta-llama/Llama-2-7b-hf"
        assert detail.display_name == "Llama-2-7b-hf"
        assert detail.family == "llama"
        assert detail.parameter_count == 7.0
        assert detail.license == "llama2"
        assert "chat" in detail.capabilities
        assert detail.source_url == "https://huggingface.co/meta-llama/Llama-2-7b-hf"


@pytest.mark.asyncio
async def test_get_model_detail_failure(provider):
    with patch.object(provider._client, "get", side_effect=Exception("not found")):
        detail = await provider.get_model_detail("nonexistent")
        assert detail is None


@pytest.mark.asyncio
async def test_download_model_success(provider):
    files_data = [
        {"path": "model-Q4_K_M.gguf", "size": 4_000_000_000},
    ]
    files_resp = _make_response(json_data=files_data)

    chunk1 = b"\x00" * 1_000_000
    chunk2 = b"\x00" * 1_000_000

    async def mock_aiter_bytes():
        yield chunk1
        yield chunk2

    download_resp = AsyncMock()
    download_resp.status_code = 200
    download_resp.headers = {"content-length": "2000000"}
    download_resp.aiter_bytes = mock_aiter_bytes
    download_resp.__aenter__ = AsyncMock(return_value=download_resp)
    download_resp.__aexit__ = AsyncMock(return_value=False)

    async def mock_get(url, **kwargs):
        if "tree" in str(url):
            return files_resp
        return download_resp

    with (
        patch.object(provider._client, "get", side_effect=mock_get),
        patch.object(provider._client, "stream", return_value=download_resp),
    ):
        progress_values = []
        result = await provider.download_model(
            "TheBloke/llama-7B-GGUF",
            on_progress=lambda p: progress_values.append(p),
        )
        assert result.success is True
        assert result.model_name == "TheBloke/llama-7B-GGUF"


@pytest.mark.asyncio
async def test_download_model_with_variant_id(provider):
    chunk = b"\x00" * 500

    async def mock_aiter_bytes():
        yield chunk

    download_resp = AsyncMock()
    download_resp.status_code = 200
    download_resp.headers = {"content-length": "500"}
    download_resp.aiter_bytes = mock_aiter_bytes
    download_resp.__aenter__ = AsyncMock(return_value=download_resp)
    download_resp.__aexit__ = AsyncMock(return_value=False)

    with patch.object(provider._client, "stream", return_value=download_resp):
        result = await provider.download_model(
            "TheBloke/llama-7B-GGUF",
            variant_id="TheBloke/llama-7B-GGUF/model-Q4_K_M.gguf",
        )
        assert result.success is True


@pytest.mark.asyncio
async def test_download_model_no_gguf_files(provider):
    files_data = [{"path": "README.md", "size": 1000}]
    resp = _make_response(json_data=files_data)
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        result = await provider.download_model("org/model")
        assert result.success is False
        assert "No GGUF" in result.error_message


@pytest.mark.asyncio
async def test_download_model_failure(provider):
    with patch.object(provider._client, "get", side_effect=Exception("network error")):
        result = await provider.download_model("org/model")
        assert result.success is False
        assert result.error_message is not None


@pytest.mark.asyncio
async def test_cancel_download_returns_false(provider):
    assert await provider.cancel_download("org/model") is False


@pytest.mark.asyncio
async def test_delete_model_returns_false(provider):
    assert await provider.delete_model("org/model") is False


@pytest.mark.asyncio
async def test_list_installed_returns_empty(provider):
    installed = await provider.list_installed()
    assert installed == []


def test_parse_gguf_filename_standard(provider):
    result = provider._parse_gguf_filename("Llama-2-7B-Q4_K_M.gguf")
    assert result is not None
    assert result["quant"] == "Q4_K_M"


def test_parse_gguf_filename_with_adapter(provider):
    result = provider._parse_gguf_filename("Llama-2-7B+adapt-Q4_K_M.gguf")
    assert result is not None


def test_parse_gguf_filename_fallback(provider):
    result = provider._parse_gguf_filename("model-Q8_0.gguf")
    assert result is not None
    assert result["quant"] == "Q8_0"


def test_infer_capabilities_text_generation(provider):
    caps = provider._infer_capabilities(["gguf", "text-generation"], "text-generation")
    assert "chat" in caps
    assert "gguf" in caps


def test_infer_capabilities_vision(provider):
    caps = provider._infer_capabilities(["vision", "image-to-text"], "image-to-text")
    assert "vision" in caps


def test_infer_capabilities_code(provider):
    caps = provider._infer_capabilities(["code", "codellama"], "text-generation")
    assert "code" in caps
    assert "chat" in caps


def test_infer_capabilities_embedding(provider):
    caps = provider._infer_capabilities(["embedding", "feature-extraction"], "feature-extraction")
    assert "embedding" in caps


def test_infer_capabilities_default(provider):
    caps = provider._infer_capabilities([], "")
    assert "chat" in caps


def test_extract_parameter_count_b(provider):
    assert provider._extract_parameter_count(["7b-parameter", "llama"]) == 7.0


def test_extract_parameter_count_m(provider):
    assert provider._extract_parameter_count(["400m-parameter"]) == 0.4


def test_extract_parameter_count_none(provider):
    assert provider._extract_parameter_count(["llama", "chat"]) is None


def test_extract_architecture(provider):
    assert provider._extract_architecture(["llama", "gguf"]) == "llama"
    assert provider._extract_architecture(["mistral-7b"]) == "mistral"
    assert provider._extract_architecture(["gemma-2b"]) == "gemma"
    assert provider._extract_architecture(["unknown-model"]) is None


def test_extract_family(provider):
    assert provider._extract_family("TheBloke/Llama-2-7B-GGUF", []) == "llama"
    assert provider._extract_family("bartowski/Mistral-7B-v0.1", []) == "mistral"
    assert provider._extract_family("org/model_name-123", []) == "modelname"


def test_extract_license_from_tag(provider):
    assert provider._extract_license(["license:apache-2.0"]) == "apache-2.0"
    assert provider._extract_license(["mit"]) == "mit"
    assert provider._extract_license(["llama", "chat"]) is None
