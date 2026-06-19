from __future__ import annotations

import os
import time
from threading import Lock

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

router = APIRouter()

_start_time = time.time()

# Request counters
_request_count = 0
_request_errors = 0
_request_latencies: list[float] = []
_metrics_lock = Lock()


def record_request(status_code: int, duration_ms: float) -> None:
    """Record a request for metrics. Called from middleware."""
    global _request_count, _request_errors
    with _metrics_lock:
        _request_count += 1
        if status_code >= 500:
            _request_errors += 1
        _request_latencies.append(duration_ms)
        # Keep only last 1000 latencies to bound memory
        if len(_request_latencies) > 1000:
            _request_latencies.pop(0)


@router.api_route("/metrics", methods=["GET", "HEAD"])
async def metrics(request: Request):
    if request.method == "HEAD":
        return
    uptime = time.time() - _start_time

    with _metrics_lock:
        total = _request_count
        errors = _request_errors
        latencies = list(_request_latencies)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0

    mem = os.popen("ps -o rss= -p " + str(os.getpid())).read().strip() if hasattr(os, "getpid") else "0"
    try:
        mem_bytes = int(mem) * 1024 if mem else 0
    except (ValueError, TypeError):
        mem_bytes = 0

    lines = [
        "# HELP cortex_uptime_seconds Application uptime",
        "# TYPE cortex_uptime_seconds gauge",
        f"cortex_uptime_seconds {uptime:.0f}",
        "# HELP cortex_memory_rss_bytes Resident memory in bytes",
        "# TYPE cortex_memory_rss_bytes gauge",
        f"cortex_memory_rss_bytes {mem_bytes}",
        "# HELP cortex_requests_total Total request count",
        "# TYPE cortex_requests_total counter",
        f"cortex_requests_total {total}",
        "# HELP cortex_request_errors_total Total request errors (5xx)",
        "# TYPE cortex_request_errors_total counter",
        f"cortex_request_errors_total {errors}",
        "# HELP cortex_request_duration_ms Request duration in milliseconds",
        "# TYPE cortex_request_duration_ms gauge",
        f"cortex_request_duration_ms {{quantile=\"avg\"}} {avg_latency:.2f}",
        f"cortex_request_duration_ms {{quantile=\"max\"}} {max_latency:.2f}",
    ]
    return PlainTextResponse("\n".join(lines) + "\n")
