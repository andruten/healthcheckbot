from datetime import datetime, timezone

import pytest

from healthchecker.application.use_cases.get_results import GetResultsUseCase
from healthchecker.domain.models.health_check import HealthCheck


class TestGetResultsUseCase:
    @pytest.fixture
    def mock_repo(self, mocker):
        repo = mocker.AsyncMock()
        now = datetime.now(timezone.utc)
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
        repo.get_by_url_id.return_value = [
            HealthCheck(
                id=10,
                url_id=1,
                http_status=200,
                ttfb_ms=50.0,
                ssl_expiration_date=now,
                ssl_days_remaining=45,
                is_healthy=True,
                error_message=None,
                checked_at=now,
            ),
        ]
        return repo

    @pytest.fixture
    def use_case(self, mock_repo):
        return GetResultsUseCase(mock_repo)

    async def test_get_latest(self, use_case, mock_repo):
        result = await use_case.get_latest(1)
        mock_repo.get_latest_by_url_id.assert_awaited_once_with(1)
        assert result is not None
        assert result.http_status == 200
        assert result.is_healthy is True

    async def test_get_history_default_limit(self, use_case, mock_repo):
        result = await use_case.get_history(1)
        mock_repo.get_by_url_id.assert_awaited_once_with(1, limit=5)
        assert len(result) == 1

    async def test_get_history_custom_limit(self, use_case, mock_repo):
        await use_case.get_history(1, limit=20)
        mock_repo.get_by_url_id.assert_awaited_with(1, limit=20)

    async def test_get_latest_no_results(self, mocker):
        repo = mocker.AsyncMock()
        repo.get_latest_by_url_id.return_value = None
        uc = GetResultsUseCase(repo)
        result = await uc.get_latest(999)
        assert result is None
