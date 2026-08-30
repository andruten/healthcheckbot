from datetime import UTC, datetime, timedelta

import pytest

from healthchecker.application.use_cases.get_stats import GetStatsUseCase
from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.services.degradation_service import (
    DegradationDetector,
    DegradationReason,
)
from healthchecker.infrastructure.config import settings


def _check(checked_at: datetime, is_healthy: bool = True, ttfb_ms: float = 50.0):
    return HealthCheck(
        id=None,
        url_id=1,
        http_status=200 if is_healthy else None,
        ttfb_ms=ttfb_ms if is_healthy else None,
        ssl_expiration_date=None,
        ssl_days_remaining=None,
        is_healthy=is_healthy,
        error_message=None,
        checked_at=checked_at,
    )


class TestGetStatsUseCase:
    @pytest.fixture
    def mock_repo(self, mocker):
        repo = mocker.AsyncMock()
        now = datetime.now(UTC)
        repo.get_latest_by_url_id.return_value = HealthCheck(
            id=10,
            url_id=1,
            http_status=200,
            ttfb_ms=50.0,
            ssl_expiration_date=now,
            ssl_days_remaining=45,
            is_healthy=True,
            error_message=None,
            checked_at=now,
        )
        repo.get_by_url_id.return_value = [_check(now)]
        repo.get_since.return_value = [_check(now)]
        return repo

    @pytest.fixture
    def use_case(self, mock_repo):
        return GetStatsUseCase(mock_repo)

    async def test_get_latest(self, use_case, mock_repo):
        result = await use_case.get_latest(1)
        mock_repo.get_latest_by_url_id.assert_awaited_once_with(1)
        assert result is not None
        assert result.http_status == 200
        assert result.is_healthy is True

    async def test_get_latest_no_results(self, mocker):
        repo = mocker.AsyncMock()
        repo.get_latest_by_url_id.return_value = None
        uc = GetStatsUseCase(repo)
        result = await uc.get_latest(999)
        assert result is None

    async def test_get_stats_uses_default_days(self, use_case, mock_repo):
        stats = await use_case.get_stats(1)
        assert mock_repo.get_since.await_args.kwargs["since"] is not None
        assert stats.total_checks == 1
        assert stats.uptime_pct == 100.0

    async def test_get_stats_custom_days(self, use_case, mock_repo):
        await use_case.get_stats(1, days=3)
        since = mock_repo.get_since.await_args.kwargs["since"]
        delta = datetime.now(UTC) - since
        assert 2.9 < delta.total_seconds() / 86400 <= 3.1

    async def test_get_stats_empty(self, mocker):
        repo = mocker.AsyncMock()
        repo.get_since.return_value = []
        uc = GetStatsUseCase(repo)
        stats = await uc.get_stats(1, days=7)
        assert stats.total_checks == 0
        assert stats.uptime_pct is None

    async def test_get_status_uses_window(self, use_case, mock_repo):
        status = await use_case.get_status(1)
        mock_repo.get_by_url_id.assert_awaited_once_with(
            1, limit=settings.degradation_window_size
        )
        assert status.is_degraded is False

    async def test_get_latest_map(self, use_case, mock_repo):
        check = _check(datetime.now(UTC))
        mock_repo.get_latest_by_url_ids.return_value = {1: check}

        result = await use_case.get_latest_map([1, 2])

        mock_repo.get_latest_by_url_ids.assert_awaited_once_with([1, 2])
        assert result == {1: check}

    async def test_get_status_map_runs_detector_per_url(self, mock_repo):
        now = datetime.now(UTC)
        history = [_check(now - timedelta(minutes=i), ttfb_ms=2000.0) for i in range(5)]
        history += [
            _check(now - timedelta(minutes=5 + i), ttfb_ms=50.0) for i in range(10)
        ]
        mock_repo.get_recent_by_url_ids.return_value = {1: [_check(now)], 2: history}
        use_case = GetStatsUseCase(
            mock_repo, degradation_detector=DegradationDetector()
        )

        result = await use_case.get_status_map([1, 2])

        mock_repo.get_recent_by_url_ids.assert_awaited_once_with(
            [1, 2], limit=settings.degradation_window_size
        )
        assert result[1].is_degraded is False
        assert result[2].is_degraded is True
        assert result[2].reason == DegradationReason.TTFB_INCREASE

    async def test_get_status_map_empty(self, use_case, mock_repo):
        mock_repo.get_recent_by_url_ids.return_value = {}

        result = await use_case.get_status_map([1])

        assert result == {}
