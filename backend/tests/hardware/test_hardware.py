"""Tests for hardware detection service."""

from backend.app.services.awareness.hardware import (
    HardwareProfile,
    _resolve_arch,
    detect_hardware,
    estimate_vram_for_gpu,
)


def test_detect_hardware_returns_profile():
    profile = detect_hardware()
    assert isinstance(profile, HardwareProfile)
    assert profile.ram_total_gb > 0
    assert profile.cpu_count > 0
    assert profile.cpu_threads > 0


def test_hardware_profile_to_dict():
    profile = HardwareProfile(
        ram_total_gb=32.0,
        ram_available_gb=24.0,
        cpu_count=8,
        cpu_threads=16,
    )
    d = profile.to_dict()
    assert d["ram_gb"] == 32.0
    assert d["cpu_count"] == 8
    assert "gpu" in d


class TestEstimateVramForGpu:
    def test_returns_expected_keys(self):
        result = estimate_vram_for_gpu(8.0, "Q4_K_M")
        assert "base_vram_gb" in result
        assert "arch_multiplier" in result
        assert "adjusted_vram_gb" in result
        assert "fits" in result
        assert "arch" in result

    def test_ampere_uses_identity_multiplier(self):
        result = estimate_vram_for_gpu(8.0, "Q4_K_M", gpu_arch="ampere", gpu_type="nvidia")
        assert result["arch_multiplier"] == 1.0
        assert result["arch"] == "ampere"
        assert result["adjusted_vram_gb"] == result["base_vram_gb"]

    def test_hopper_reduces_vram_estimate(self):
        result = estimate_vram_for_gpu(8.0, "Q4_K_M", gpu_arch="hopper", gpu_type="nvidia")
        assert result["arch_multiplier"] < 1.0
        assert result["adjusted_vram_gb"] < result["base_vram_gb"]

    def test_turing_increases_vram_estimate(self):
        result = estimate_vram_for_gpu(8.0, "Q4_K_M", gpu_arch="turing", gpu_type="nvidia")
        assert result["arch_multiplier"] > 1.0
        assert result["adjusted_vram_gb"] > result["base_vram_gb"]

    def test_apple_silicon_uses_lower_multiplier_and_overhead(self):
        result = estimate_vram_for_gpu(8.0, "Q4_K_M", gpu_type="apple_metal")
        assert result["arch"] == "apple_silicon"
        assert result["arch_multiplier"] == 0.90
        # Apple overhead is 0.15 GB (vs 0.0 for others)
        ampere = estimate_vram_for_gpu(8.0, "Q4_K_M", gpu_arch="ampere", gpu_type="nvidia")
        assert result["adjusted_vram_gb"] < ampere["adjusted_vram_gb"]

    def test_fits_true_when_enough_vram(self):
        result = estimate_vram_for_gpu(7.0, "Q4_K_M", gpu_arch="ampere", gpu_type="nvidia", vram_available_gb=16.0)
        assert result["fits"] is True

    def test_fits_false_when_insufficient_vram(self):
        result = estimate_vram_for_gpu(70.0, "Q4_K_M", gpu_arch="ampere", gpu_type="nvidia", vram_available_gb=16.0)
        assert result["fits"] is False

    def test_fits_none_when_vram_unknown(self):
        result = estimate_vram_for_gpu(7.0, "Q4_K_M")
        assert result["fits"] is None

    def test_unknown_arch_uses_identity(self):
        result = estimate_vram_for_gpu(8.0, "Q4_K_M", gpu_arch="some_new_arch", gpu_type="nvidia")
        assert result["arch_multiplier"] == 1.0
        assert result["arch"] == "some_new_arch"

    def test_different_quantizations_produce_different_sizes(self):
        q8 = estimate_vram_for_gpu(8.0, "Q8_0", gpu_arch="ampere", gpu_type="nvidia")
        q4 = estimate_vram_for_gpu(8.0, "Q4_K_M", gpu_arch="ampere", gpu_type="nvidia")
        assert q8["base_vram_gb"] > q4["base_vram_gb"]

    def test_context_length_affects_estimate(self):
        short = estimate_vram_for_gpu(8.0, "Q4_K_M", gpu_arch="ampere", gpu_type="nvidia", context_length=2048)
        long = estimate_vram_for_gpu(8.0, "Q4_K_M", gpu_arch="ampere", gpu_type="nvidia", context_length=32768)
        assert long["base_vram_gb"] > short["base_vram_gb"]

    def test_ada_lovelace_reduces_vram(self):
        result = estimate_vram_for_gpu(8.0, "Q4_K_M", gpu_arch="ada_lovelace", gpu_type="nvidia")
        assert result["arch_multiplier"] == 0.95
        assert result["adjusted_vram_gb"] < result["base_vram_gb"]


class TestResolveArch:
    def test_apple_metal_returns_apple_silicon(self):
        assert _resolve_arch(None, "apple_metal") == "apple_silicon"

    def test_nvidia_with_arch(self):
        assert _resolve_arch("ampere", "nvidia") == "ampere"

    def test_nvidia_without_arch(self):
        assert _resolve_arch(None, "nvidia") == "unknown"

    def test_no_gpu(self):
        assert _resolve_arch(None, "none") == "unknown"
