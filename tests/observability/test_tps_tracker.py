"""Tests for TPS tracking — P07 Task 2."""

from __future__ import annotations

import time

from backend.app.agents.tps_tracker import TPSMeasurement, TPSTracker


class TestTPSTrackerBasic:
    def test_start_creates_measurement(self):
        tracker = TPSTracker()
        tracker.start()
        assert tracker._measurement is not None
        assert tracker._measurement.start_time > 0

    def test_on_token_increments(self):
        tracker = TPSTracker()
        tracker.start()
        tracker.on_token()
        tracker.on_token()
        tracker.on_token()
        assert tracker._measurement.total_tokens == 3

    def test_on_token_batch(self):
        tracker = TPSTracker()
        tracker.start()
        tracker.on_token(count=10)
        assert tracker._measurement.total_tokens == 10

    def test_first_token_latency(self):
        tracker = TPSTracker()
        tracker.start()
        time.sleep(0.01)
        tracker.on_token()
        assert tracker._measurement.first_token_latency_ms >= 5  # at least ~10ms

    def test_finish_returns_measurement(self):
        tracker = TPSTracker()
        tracker.start()
        tracker.on_token(count=5)
        time.sleep(0.01)
        result = tracker.finish()
        assert isinstance(result, TPSMeasurement)
        assert result.total_tokens == 5
        assert result.total_duration > 0
        assert result.avg_tps > 0


class TestTPSTrackerInstantaneous:
    def test_instantaneous_tps(self):
        tracker = TPSTracker()
        tracker.start()
        for _ in range(10):
            tracker.on_token()
        tps = tracker.get_instantaneous_tps()
        assert tps >= 10  # 10 tokens just sent

    def test_instantaneous_window_decay(self):
        tracker = TPSTracker()
        tracker.start()
        tracker.on_token(count=5)
        # Wait a bit, tokens should still be in window
        time.sleep(0.1)
        tps = tracker.get_instantaneous_tps()
        assert tps >= 5


class TestTPSTrackerReset:
    def test_reset_clears_state(self):
        tracker = TPSTracker()
        tracker.start()
        tracker.on_token(count=10)
        tracker.reset()
        assert tracker._measurement.total_tokens == 0
        assert len(tracker._instantaneous_window) == 0
