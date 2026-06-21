import pytest


def test_prometheus_metrics(client):
    resp = client.get("/api/v1/metrics")
    assert resp.status_code == 200
    text = resp.text
    assert "cortex_uptime_seconds" in text
    assert "cortex_memory_rss_bytes" in text
    assert "cortex_requests_total" in text
    assert "cortex_request_errors_total" in text
    assert "# HELP" in text
    assert "# TYPE" in text


def test_prometheus_metrics_head(client):
    resp = client.head("/api/v1/metrics")
    assert resp.status_code == 200
