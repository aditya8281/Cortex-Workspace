"""Enhanced hardware detection for inference-aware recommendations."""

from __future__ import annotations

import logging
import platform
import subprocess
from dataclasses import dataclass

import psutil

logger = logging.getLogger(__name__)

# GPU memory bandwidth database (GB/s) - common GPUs
GPU_BANDWIDTH_DB: dict[str, float] = {
    # NVIDIA
    "RTX 4090": 1008.0,
    "RTX 4080": 717.0,
    "RTX 4070 Ti": 504.0,
    "RTX 4070": 504.0,
    "RTX 3090": 936.0,
    "RTX 3080": 760.0,
    "RTX 3070": 448.0,
    "RTX 3060": 360.0,
    "RTX 2080 Ti": 616.0,
    "RTX 2080": 448.0,
    "RTX 2070": 448.0,
    "RTX 2060": 336.0,
    "A100": 2039.0,
    "A100 80GB": 2039.0,
    "A100 40GB": 1555.0,
    "A6000": 768.0,
    "L40": 864.0,
    "L40S": 864.0,
    "H100": 3350.0,
    "H100 80GB": 3350.0,
    "H200": 4800.0,
    "Tesla T4": 300.0,
    "Tesla V100": 900.0,
    "Tesla P100": 732.0,
    # Apple Silicon
    "M1": 68.25,
    "M1 Pro": 200.0,
    "M1 Max": 400.0,
    "M1 Ultra": 800.0,
    "M2": 100.0,
    "M2 Pro": 200.0,
    "M2 Max": 400.0,
    "M2 Ultra": 800.0,
    "M3": 100.0,
    "M3 Pro": 150.0,
    "M3 Max": 400.0,
    "M4": 120.0,
    "M4 Pro": 170.0,
    "M4 Max": 546.0,
}

# GPU compute capability database
GPU_COMPUTE_DB: dict[str, str] = {
    "RTX 4090": "8.9",
    "RTX 4080": "8.9",
    "RTX 4070 Ti": "8.9",
    "RTX 4070": "8.9",
    "RTX 3090": "8.6",
    "RTX 3080": "8.6",
    "RTX 3070": "8.6",
    "RTX 3060": "8.6",
    "A100": "8.0",
    "H100": "9.0",
}


@dataclass
class HardwareProfile:
    """Complete hardware profile for inference recommendations."""

    # CPU
    cpu_count: int = 0
    cpu_threads: int = 0
    cpu_freq_mhz: float = 0.0
    cpu_arch: str = "x86_64"

    # System RAM
    ram_total_gb: float = 0.0
    ram_available_gb: float = 0.0

    # GPU (primary)
    gpu_available: bool = False
    gpu_name: str | None = None
    gpu_type: str = "none"  # "nvidia", "amd", "apple_metal", "none"
    gpu_driver_version: str | None = None
    vram_total_gb: float = 0.0
    vram_available_gb: float = 0.0
    gpu_memory_bandwidth_gbps: float | None = None
    gpu_compute_capability: str | None = None
    gpu_arch: str | None = None

    # Apple Silicon specifics
    apple_unified_memory_gb: float | None = None
    apple_gpu_cores: int | None = None
    apple_neural_engine: bool = False

    # Disk
    disk_free_gb: float = 0.0

    # Compute capability flags
    supports_cuda: bool = False
    supports_metal: bool = False
    supports_vulkan: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "ram_gb": round(self.ram_total_gb, 1),
            "ram_available_gb": round(self.ram_available_gb, 1),
            "ram_percent": round(
                ((self.ram_total_gb - self.ram_available_gb) / self.ram_total_gb * 100) if self.ram_total_gb > 0 else 0,
                1,
            ),
            "cpu_count": self.cpu_count,
            "cpu_threads": self.cpu_threads,
            "cpu_freq_mhz": self.cpu_freq_mhz,
            "cpu_arch": self.cpu_arch,
            "gpu": {
                "available": self.gpu_available,
                "name": self.gpu_name,
                "type": self.gpu_type,
                "vram_gb": round(self.vram_total_gb, 1),
                "vram_available_gb": round(self.vram_available_gb, 1),
                "memory_bandwidth_gbps": self.gpu_memory_bandwidth_gbps,
                "compute_capability": self.gpu_compute_capability,
                "arch": self.gpu_arch,
            },
            "disk_free_gb": round(self.disk_free_gb, 1),
            "supports_cuda": self.supports_cuda,
            "supports_metal": self.supports_metal,
        }


def detect_hardware() -> HardwareProfile:
    """Detect complete system hardware profile."""
    profile = HardwareProfile()

    # CPU
    profile.cpu_count = psutil.cpu_count(logical=False) or 1
    profile.cpu_threads = psutil.cpu_count(logical=True) or 1
    cpu_freq = psutil.cpu_freq()
    if cpu_freq:
        profile.cpu_freq_mhz = cpu_freq.current
    profile.cpu_arch = platform.machine()

    # RAM
    mem = psutil.virtual_memory()
    profile.ram_total_gb = mem.total / (1024**3)
    profile.ram_available_gb = mem.available / (1024**3)

    # GPU - NVIDIA
    profile.gpu_type = _detect_nvidia_gpu(profile)

    # GPU - Apple Metal
    if profile.gpu_type == "none":
        profile.gpu_type = _detect_apple_gpu(profile)

    # Disk
    try:
        disk = psutil.disk_usage(".")
        profile.disk_free_gb = disk.free / (1024**3)
    except Exception:
        pass

    return profile


def _detect_nvidia_gpu(profile: HardwareProfile) -> str:
    """Detect NVIDIA GPU via nvidia-smi."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return "none"

        parts = result.stdout.strip().split(", ")
        if len(parts) < 5:
            return "none"

        gpu_name = parts[0].strip()
        driver_version = parts[1].strip()
        vram_total_mb = float(parts[2].strip())
        vram_used_mb = float(parts[3].strip())

        profile.gpu_available = True
        profile.gpu_name = gpu_name
        profile.gpu_driver_version = driver_version
        profile.vram_total_gb = vram_total_mb / 1024
        profile.vram_available_gb = (vram_total_mb - vram_used_mb) / 1024
        profile.supports_cuda = True

        # Look up bandwidth and compute capability
        profile.gpu_memory_bandwidth_gbps = _lookup_gpu_bandwidth(gpu_name)
        profile.gpu_compute_capability = _lookup_compute_capability(gpu_name)
        profile.gpu_arch = _infer_gpu_arch(gpu_name)

        return "nvidia"
    except Exception as e:
        logger.debug("NVIDIA GPU detection failed: %s", e)
        return "none"


def _detect_apple_gpu(profile: HardwareProfile) -> str:
    """Detect Apple Silicon GPU."""
    if platform.system() != "Darwin":
        return "none"

    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return "none"

        for line in result.stdout.split("\n"):
            if "Chipset Model:" in line:
                gpu_name = line.split(":", 1)[1].strip()
                profile.gpu_available = True
                profile.gpu_name = gpu_name
                profile.supports_metal = True

                # Estimate unified memory
                profile.apple_unified_memory_gb = profile.ram_total_gb

                # Look up bandwidth
                profile.gpu_memory_bandwidth_gbps = _lookup_gpu_bandwidth(gpu_name)

                return "apple_metal"
    except Exception:
        pass

    return "none"


def _lookup_gpu_bandwidth(gpu_name: str) -> float | None:
    """Look up GPU memory bandwidth from database."""
    for key, bandwidth in GPU_BANDWIDTH_DB.items():
        if key.lower() in gpu_name.lower():
            return bandwidth
    return None


def _lookup_compute_capability(gpu_name: str) -> str | None:
    """Look up GPU compute capability."""
    for key, cc in GPU_COMPUTE_DB.items():
        if key.lower() in gpu_name.lower():
            return cc
    return None


def _infer_gpu_arch(gpu_name: str) -> str | None:
    """Infer GPU architecture from name."""
    name_lower = gpu_name.lower()
    if "4090" in name_lower or "4080" in name_lower or "4070" in name_lower:
        return "ada_lovelace"
    if "3090" in name_lower or "3080" in name_lower or "3070" in name_lower or "3060" in name_lower:
        return "ampere"
    if "2080" in name_lower or "2070" in name_lower or "2060" in name_lower:
        return "turing"
    if "a100" in name_lower or "a6000" in name_lower:
        return "ampere"
    if "h100" in name_lower or "h200" in name_lower:
        return "hopper"
    if "l40" in name_lower:
        return "ada_lovelace"
    if "t4" in name_lower:
        return "turing"
    if "v100" in name_lower:
        return "volta"
    return None


# Architecture-specific VRAM overhead multipliers (relative to baseline 1.0).
# Newer architectures have more efficient memory usage (compression, cache).
# Apple Silicon uses unified memory with different allocation patterns.
_ARCH_VRAM_MULTIPLIER: dict[str, float] = {
    "hopper": 0.92,
    "ada_lovelace": 0.95,
    "ampere": 1.0,
    "turing": 1.03,
    "volta": 1.06,
    "apple_silicon": 0.90,
}

# Architecture-specific overhead adjustments in GB.
# Unified memory on Apple Silicon avoids some duplication.
_ARCH_OVERHEAD_GB: dict[str, float] = {
    "apple_silicon": 0.15,
}


def _resolve_arch(gpu_arch: str | None, gpu_type: str) -> str:
    """Map hardware profile to architecture key for overhead lookups."""
    if gpu_type == "apple_metal":
        return "apple_silicon"
    if gpu_arch:
        return gpu_arch
    return "unknown"


def estimate_vram_for_gpu(
    parameter_count: float,
    quantization: str,
    gpu_arch: str | None = None,
    gpu_type: str = "none",
    vram_available_gb: float | None = None,
    context_length: int = 4096,
) -> dict[str, float | str | None]:
    """Estimate VRAM with architecture-aware overhead and efficiency.

    Returns a dict with keys:
        - base_vram_gb: model + generic overhead before arch adjustment
        - arch_multiplier: architecture efficiency multiplier applied
        - adjusted_vram_gb: final adjusted estimate
        - fits: whether the model fits in available VRAM (None if unknown)
        - arch: resolved architecture key used
    """
    from backend.app.services.quantization_db import QuantizationService

    svc = QuantizationService()
    base_vram = svc.estimate_vram_gb(parameter_count, quantization, context_length)

    arch_key = _resolve_arch(gpu_arch, gpu_type)
    multiplier = _ARCH_VRAM_MULTIPLIER.get(arch_key, 1.0)

    adjusted = base_vram * multiplier

    # Apply architecture-specific fixed overhead (e.g., Apple unified memory)
    arch_overhead = _ARCH_OVERHEAD_GB.get(arch_key, 0.0)
    adjusted += arch_overhead

    fits: bool | None = None
    if vram_available_gb is not None and vram_available_gb > 0:
        fits = adjusted <= vram_available_gb

    return {
        "base_vram_gb": round(base_vram, 3),
        "arch_multiplier": multiplier,
        "adjusted_vram_gb": round(adjusted, 3),
        "fits": fits,
        "arch": arch_key,
    }
