"""Tests for provider base interface."""

import pytest

from backend.app.services.providers.base import (
    ProviderAdapter,
    ProviderDownloadResult,
    ProviderModelInfo,
    ProviderVariantInfo,
)


def test_provider_model_info_defaults():
    info = ProviderModelInfo(provider_model_id="test", display_name="Test")
    assert info.capabilities == []
    assert info.tags == []
    assert info.extra_metadata == {}


def test_provider_variant_info_defaults():
    info = ProviderVariantInfo(variant_id="test", quantization="Q4_K_M")
    assert info.extra_metadata == {}


def test_provider_download_result_defaults():
    result = ProviderDownloadResult(success=True)
    assert result.file_path is None
    assert result.error_message is None


def test_provider_adapter_is_abstract():
    with pytest.raises(TypeError):
        ProviderAdapter()
