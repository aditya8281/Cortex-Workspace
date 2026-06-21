"""Tests for quantization database service."""

from backend.app.services.quantization_db import QuantizationService


def test_get_quant_info():
    svc = QuantizationService()
    info = svc.get_quant_info("Q4_K_M")
    assert info is not None
    assert info["quality_score"] == 90.0
    assert info["bits_per_param"] == 4.0


def test_get_quant_info_case_insensitive():
    svc = QuantizationService()
    assert svc.get_quant_info("q4_k_m") is not None
    assert svc.get_quant_info("Q8_0") is not None


def test_estimate_vram_gb():
    svc = QuantizationService()
    vram = svc.estimate_vram_gb(8.0, "Q4_K_M")
    assert 3.0 < vram < 6.0  # 8B model Q4 should be ~4-5GB


def test_estimate_vram_smaller_with_lower_quant():
    svc = QuantizationService()
    vram_q8 = svc.estimate_vram_gb(8.0, "Q8_0")
    vram_q4 = svc.estimate_vram_gb(8.0, "Q4_K_M")
    assert vram_q8 > vram_q4


def test_recommend_quantization_fits():
    svc = QuantizationService()
    recs = svc.recommend_quantization(8.0, 12.0)
    assert len(recs) > 0
    assert all(r["vram_required_gb"] <= 12.0 for r in recs)


def test_recommend_quantization_excludes_too_large():
    svc = QuantizationService()
    recs = svc.recommend_quantization(70.0, 8.0)
    assert len(recs) == 0  # 70B model won't fit in 8GB
