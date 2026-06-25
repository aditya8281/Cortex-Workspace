"""Tests for health check probes."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.daemon.health import (
    HealthProbeResult,
    HealthReport,
    check_all,
    probe_database,
    probe_qdrant,
    probe_redis,
)


class TestHealthProbeResult:
    def test_basic_probe(self):
        result = HealthProbeResult(name="test", healthy=True, detail="ok")
        assert result.name == "test"
        assert result.healthy is True
        assert result.detail == "ok"


class TestHealthReport:
    def test_summary_ok(self):
        report = HealthReport(
            healthy=True,
            probes=[
                HealthProbeResult(name="a", healthy=True),
                HealthProbeResult(name="b", healthy=True),
            ],
        )
        assert report.summary == "2/2 dependencies healthy"

    def test_summary_partial(self):
        report = HealthReport(
            healthy=False,
            probes=[
                HealthProbeResult(name="a", healthy=True),
                HealthProbeResult(name="b", healthy=False),
            ],
        )
        assert report.summary == "1/2 dependencies healthy"

    def test_to_dict(self):
        report = HealthReport(
            healthy=True,
            probes=[
                HealthProbeResult(name="test", healthy=True, detail="ok", metadata={"count": 1}),
            ],
        )
        d = report.to_dict()
        assert d["healthy"] is True
        assert d["summary"] == "1/1 dependencies healthy"
        assert d["probes"][0]["name"] == "test"
        assert d["probes"][0]["metadata"]["count"] == 1


class TestProbeDatabase:
    @patch("backend.app.db.session.SessionLocal")
    async def test_healthy(self, mock_session_cls):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 1
        mock_session_cls.return_value = mock_db

        result = await probe_database(timeout=2.0)
        assert result.healthy is True
        assert "responsive" in result.detail.lower()

    @patch("backend.app.db.session.SessionLocal")
    async def test_query_failure(self, mock_session_cls):
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB down")
        mock_session_cls.return_value = mock_db

        result = await probe_database(timeout=2.0)
        assert result.healthy is False

    @patch("backend.app.db.session.SessionLocal")
    async def test_timeout(self, mock_session_cls):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 1

        async def slow_run(*args, **kwargs):
            await asyncio.sleep(10)
            return None

        mock_session_cls.return_value = mock_db

        # Make the run_in_executor really slow
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor.side_effect = lambda *a: asyncio.sleep(10)
            result = await probe_database(timeout=0.05)

            assert result.healthy is False


class TestProbeRedis:
    async def test_healthy(self):
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        with patch("backend.app.core.redis.redis_cache", mock_redis):
            result = await probe_redis(timeout=2.0)
            assert result.healthy is True

    async def test_no_redis_configured(self):
        with patch("backend.app.core.redis.redis_cache", None):
            result = await probe_redis(timeout=2.0)
            assert result.healthy is False
            assert "not configured" in result.detail.lower()

    async def test_ping_fails(self):
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Redis down")
        with patch("backend.app.core.redis.redis_cache", mock_redis):
            result = await probe_redis(timeout=2.0)
            assert result.healthy is False
            assert "down" in result.detail.lower()

    async def test_timeout(self):
        mock_redis = AsyncMock()

        async def slow_ping():
            await asyncio.sleep(10)
            return True

        mock_redis.ping = slow_ping
        with patch("backend.app.core.redis.redis_cache", mock_redis):
            result = await probe_redis(timeout=0.05)
            assert result.healthy is False
            assert "timed out" in result.detail.lower()


class TestProbeQdrant:
    async def test_not_available(self):
        with patch("backend.app.daemon.health._get_qdrant_client", return_value=None):
            result = await probe_qdrant(timeout=2.0)
            assert result.healthy is False

    async def test_healthy(self):
        mock_qdrant = MagicMock()
        mock_qdrant.list_collections.return_value = ["coll1", "coll2"]

        with patch("backend.app.daemon.health._get_qdrant_client", return_value=mock_qdrant):
            result = await probe_qdrant(timeout=2.0)
            assert result.healthy is True
            assert result.metadata["collection_count"] == 2

    async def test_timeout(self):
        """Timeout is handled gracefully (probe returns unhealthy)."""
        import asyncio
        from unittest.mock import AsyncMock

        # AsyncMock properly returns coroutines when side_effect is an async function
        async def _hang():
            await asyncio.sleep(30)
            return "never"

        mock_get = AsyncMock(side_effect=_hang)
        with patch("backend.app.daemon.health._get_qdrant_client", mock_get):
            result = await probe_qdrant(timeout=0.05)
            assert result.healthy is False, f"Expected unhealthy, got: {result}"
            assert "timed out" in result.detail.lower()


class TestCheckAll:
    async def test_all_healthy(self):
        with (
            patch(
                "backend.app.daemon.health.probe_database",
                return_value=HealthProbeResult(name="database", healthy=True),
            ),
            patch("backend.app.daemon.health.probe_redis", return_value=HealthProbeResult(name="redis", healthy=True)),
            patch(
                "backend.app.daemon.health.probe_qdrant", return_value=HealthProbeResult(name="qdrant", healthy=True)
            ),
        ):
            report = await check_all()
            assert report.healthy is True
            assert len(report.probes) == 3

    async def test_one_unhealthy(self):
        with (
            patch(
                "backend.app.daemon.health.probe_database",
                return_value=HealthProbeResult(name="database", healthy=True),
            ),
            patch("backend.app.daemon.health.probe_redis", return_value=HealthProbeResult(name="redis", healthy=False)),
            patch(
                "backend.app.daemon.health.probe_qdrant", return_value=HealthProbeResult(name="qdrant", healthy=True)
            ),
        ):
            report = await check_all()
            assert report.healthy is False

    async def test_handles_exception(self):
        with (
            patch("backend.app.daemon.health.probe_database", side_effect=ValueError("boom")),
            patch("backend.app.daemon.health.probe_redis", return_value=HealthProbeResult(name="redis", healthy=True)),
            patch(
                "backend.app.daemon.health.probe_qdrant", return_value=HealthProbeResult(name="qdrant", healthy=True)
            ),
        ):
            report = await check_all()
            assert report.healthy is False
            assert len(report.probes) == 3
