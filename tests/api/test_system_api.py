"""Tests for system API — health checks and system information."""

from unittest.mock import patch

HEADERS = {"Authorization": "Bearer fake-token"}


@patch("backend.app.api.v1.system.system.psutil")
@patch("backend.app.api.v1.system.system.get_disk_info")
@patch("backend.app.api.v1.system.system.get_gpu_info")
@patch("backend.app.api.v1.system.system.get_ram_info")
def test_system_metrics(mock_ram, mock_gpu, mock_disk, mock_psutil, client, mock_auth):
    mock_ram.return_value = {"total_gb": 16.0, "available_gb": 8.0}
    mock_gpu.return_value = {"name": "RTX 3080", "type": "cuda", "utilization_gpu": 75.0, "detected": True}
    mock_disk.return_value = {"total_gb": 500.0, "used_gb": 200.0, "percent": 40.0}
    mock_psutil.cpu_percent.return_value = 45.0
    mock_psutil.process_iter.return_value = []
    mock_psutil.STATUS_RUNNING = "running"

    resp = client.get("/api/v1/system/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cpu_percent"] == 45.0
    assert data["ram_total_gb"] == 16.0
    assert data["ram_used_gb"] == 8.0
    assert data["gpu_name"] == "RTX 3080"
    assert data["disk_total_gb"] == 500.0
    assert isinstance(data["processes"], list)


def test_system_logs(client, mock_auth):
    resp = client.get("/api/v1/system/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["logs"], list)
    assert isinstance(data["total"], int)
