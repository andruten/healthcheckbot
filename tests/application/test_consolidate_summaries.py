from datetime import date, datetime, timezone

import pytest

from healthchecker.application.use_cases.consolidate_summaries import (
    ConsolidateDailySummariesUseCase,
)
from healthchecker.domain.models.health_check import HealthCheck


class TestConsolidateDailySummariesUseCase:
    @pytest.fixture
    def now(self):
        return datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)

    @pytest.fixture
    def raw_checks(self, now):
        return [
            HealthCheck(
                id=1,
                url_id=1,
                http_status=200,
                ttfb_ms=100.0,
                ssl_expiration_date=now,
                ssl_days_remaining=50,
                is_healthy=True,
                error_message=None,
                checked_at=now,
            ),
            HealthCheck(
                id=2,
                url_id=1,
                http_status=200,
                ttfb_ms=150.0,
                ssl_expiration_date=now,
                ssl_days_remaining=50,
                is_healthy=True,
                error_message=None,
                checked_at=datetime(2026, 6, 10, 12, 1, 0, tzinfo=timezone.utc),
            ),
            HealthCheck(
                id=3,
                url_id=1,
                http_status=503,
                ttfb_ms=None,
                ssl_expiration_date=None,
                ssl_days_remaining=None,
                is_healthy=False,
                error_message="Timeout",
                checked_at=datetime(2026, 6, 10, 12, 2, 0, tzinfo=timezone.utc),
            ),
        ]

    @pytest.fixture
    def mocks(self, mocker, raw_checks):
        health_repo = mocker.AsyncMock()
        health_repo.get_dates_needing_consolidation.return_value = [
            (1, date(2026, 6, 10))
        ]
        health_repo.get_raw_for_date.return_value = raw_checks
        health_repo.purge_older_than.return_value = 3

        summary_repo = mocker.AsyncMock()
        summary_repo.get_by_url_id_and_date.return_value = None
        return health_repo, summary_repo

    @pytest.fixture
    def use_case(self, mocks):
        health_repo, summary_repo = mocks
        return ConsolidateDailySummariesUseCase(
            health_check_repo=health_repo,
            summary_repo=summary_repo,
            retention_days=7,
        )

    async def test_consolidates_and_purges(self, use_case, mocks):
        health_repo, summary_repo = mocks
        count = await use_case.execute()

        assert count == 1
        health_repo.get_dates_needing_consolidation.assert_awaited_once()
        health_repo.get_raw_for_date.assert_awaited_once_with(1, date(2026, 6, 10))
        summary_repo.save.assert_awaited_once()
        health_repo.purge_older_than.assert_awaited_once()

    async def test_saved_summary_values(self, use_case, mocks, raw_checks):
        _, summary_repo = mocks
        await use_case.execute()
        saved = summary_repo.save.call_args[0][0]

        assert saved.url_id == 1
        assert saved.summary_date == date(2026, 6, 10)
        assert saved.checks_count == 3
        assert saved.avg_ttfb_ms == 125.0
        assert saved.min_ttfb_ms == 100.0
        assert saved.max_ttfb_ms == 150.0
        assert saved.min_ssl_days_remaining == 50
        assert saved.healthy_count == 2
        assert saved.unhealthy_count == 1
        assert saved.last_http_status == 503

    async def test_no_pending_consolidation(self, mocker):
        health_repo = mocker.AsyncMock()
        health_repo.get_dates_needing_consolidation.return_value = []
        summary_repo = mocker.AsyncMock()
        uc = ConsolidateDailySummariesUseCase(health_repo, summary_repo)

        count = await uc.execute()
        assert count == 0
        health_repo.get_raw_for_date.assert_not_called()
        summary_repo.save.assert_not_called()
