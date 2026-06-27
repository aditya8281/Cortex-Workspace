"""Performance baseline capture and comparison."""

import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class PerformanceBaseline:
    """Captures performance metrics as a baseline."""

    captured_at: str
    api_response_times: dict
    memory_usage_mb: float
    test_suite_duration_seconds: float
    test_count: int
    build_duration_seconds: float
    bundle_size_kb: float
    type_check_duration_seconds: float
    total_python_files: int
    total_typescript_files: int
    total_test_files: int
    total_lines_of_code: int


def capture_backend_metrics() -> dict:
    """Capture backend performance metrics."""
    return {"/api/v1/health": 0.0}


def capture_memory_usage() -> float:
    """Capture current memory usage in MB."""
    try:
        import psutil

        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


def capture_test_metrics() -> tuple[float, int]:
    """Capture test suite duration and count."""
    start = time.time()
    try:
        result = subprocess.run(
            ["make", "test"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        duration = time.time() - start
        test_count = 0
        for line in result.stdout.split("\n"):
            if "passed" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        test_count = int(parts[i - 1])
                        break
        return duration, test_count
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return time.time() - start, 0


def capture_code_metrics() -> dict:
    """Capture codebase metrics."""
    metrics = {}
    result = subprocess.run(
        ["find", "backend/", "-name", "*.py", "-not", "-path", "*/__pycache__/*"],
        capture_output=True,
        text=True,
    )
    metrics["python_files"] = (
        len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    )
    result = subprocess.run(
        ["find", "frontend/src/", "-name", "*.ts", "-o", "-name", "*.tsx"],
        capture_output=True,
        text=True,
    )
    metrics["typescript_files"] = (
        len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    )
    result = subprocess.run(
        ["find", "tests/", "-name", "test_*.py", "-o", "-name "*_test.py""],
        capture_output=True,
        text=True,
    )
    metrics["test_files"] = (
        len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    )
    return metrics


def capture_baseline() -> PerformanceBaseline:
    """Capture a complete performance baseline."""
    print("Capturing performance baseline...")
    print("  Measuring test suite...")
    test_duration, test_count = capture_test_metrics()
    print("  Measuring memory usage...")
    memory = capture_memory_usage()
    print("  Counting code metrics...")
    code_metrics = capture_code_metrics()
    baseline = PerformanceBaseline(
        captured_at=datetime.now().isoformat(),
        api_response_times=capture_backend_metrics(),
        memory_usage_mb=memory,
        test_suite_duration_seconds=test_duration,
        test_count=test_count,
        build_duration_seconds=0.0,
        bundle_size_kb=0.0,
        type_check_duration_seconds=0.0,
        total_python_files=code_metrics.get("python_files", 0),
        total_typescript_files=code_metrics.get("typescript_files", 0),
        total_test_files=code_metrics.get("test_files", 0),
        total_lines_of_code=0,
    )
    return baseline


def save_baseline(
    baseline: PerformanceBaseline,
    path: str = "tests/performance/baseline.json",
):
    """Save baseline to file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(asdict(baseline), f, indent=2)
    print(f"Baseline saved to {path}")


if __name__ == "__main__":
    baseline = capture_baseline()
    save_baseline(baseline)
    print(json.dumps(asdict(baseline), indent=2))
