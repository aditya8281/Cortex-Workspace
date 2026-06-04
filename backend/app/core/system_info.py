"""
Cross-platform system information utility.

Provides OS-agnostic way to get CPU, RAM, GPU, and system info.
NO OS-specific paths or direct /proc access.
"""

import subprocess
import platform
from typing import Dict, Any

logger = None  # Will be imported to avoid circular imports

try:
    import psutil
except ImportError:
    psutil = None


def get_system_info() -> str:
    """Get system info (OS, version) safely."""
    try:
        return f"{platform.system()} {platform.release()}"
    except Exception:
        return "Unknown OS"


def get_cpu_info() -> str:
    """
    Get CPU model name safely (cross-platform).
    
    Uses psutil library as primary source, falls back to platform.processor().
    NO direct /proc access.
    """
    try:
        # Try psutil first (most reliable)
        if psutil:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                return f"{cpu_freq.current:.2f} MHz"
        
        # Fallback to platform module
        processor = platform.processor()
        if processor:
            return processor
        
        # Last resort - return OS-specific safe info
        system = platform.system()
        if system == "Darwin":
            # macOS
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()
        
        return "Unknown CPU"
    except Exception:
        return platform.processor() or "Unknown CPU"


def get_ram_info() -> Dict[str, float]:
    """
    Get RAM info safely (cross-platform).
    
    Uses psutil library.
    NO direct /proc access.
    
    Returns:
        Dict with 'total_gb' and 'available_gb' keys
    """
    try:
        if psutil:
            mem = psutil.virtual_memory()
            return {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
            }
    except Exception:
        pass
    
    # Default fallback
    return {"total_gb": 16.0, "available_gb": 8.0}


def get_gpu_info() -> Dict[str, Any]:
    """
    Get GPU info safely (cross-platform).
    
    Tries NVIDIA GPUs and Apple Metal.
    Returns empty dict if no GPU detected.
    """
    try:
        # Try NVIDIA GPU
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            if len(parts) >= 3:
                return {
                    "type": "NVIDIA",
                    "name": parts[0].strip(),
                    "driver_version": parts[1].strip(),
                    "memory_gb": float(parts[2].strip().split()[0]) / 1024,
                }
    except Exception:
        pass
    
    try:
        # Try Apple Metal GPU
        if platform.system() == "Darwin":
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "GPU" in result.stdout:
                return {
                    "type": "Apple Metal",
                    "detected": True,
                }
    except Exception:
        pass
    
    return {}


def get_disk_info(path: str = ".") -> Dict[str, float]:
    """
    Get disk usage info safely (cross-platform).
    
    Uses psutil library.
    """
    try:
        if psutil:
            usage = psutil.disk_usage(path)
            return {
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent,
            }
    except Exception:
        pass
    
    return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}


def get_python_info() -> Dict[str, Any]:
    """Get Python version and implementation info."""
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "compiler": platform.python_compiler(),
    }


def get_os_info() -> Dict[str, Any]:
    """Get complete OS info (safe, cross-platform)."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.architecture()[0],
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
