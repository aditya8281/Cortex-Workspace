"""Tests for hardware detection service."""

from backend.app.services.hardware import HardwareProfile, detect_hardware


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
