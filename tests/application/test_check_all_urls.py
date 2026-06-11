from datetime import datetime, timezone

import pytest

from healthchecker.application.use_cases.check_all_urls import CheckAllUrlsUseCase
from healthchecker.domain.models.url import Url
from healthchecker.domain.models.alert import AlertType
from healthchecker.infrastructure.checker.ssl_checker import SslInfo


HTTP_OK = (200, 100.0, None)
HTTP_503 = (503, 50.0, None)
TIMEOUT = (None, None, "Timeout")


class TestCheckAllUrlsUseCase:
    @pytest.fixture
    def active_urls(self):
        return [
            Url(
                id=1,
                name="Example",
                url="https://example.com",
                alert_before_days=30,
                is_active=True,
                created_at=None,
                updated_at=None,
            ),
            Url(
                id=2,
                name="HttpOnly",
                url="http://httponly.com",
                alert_before_days=30,
                is_active=True,
                created_at=None,
                updated_at=None,
            ),
        ]

    @pytest.fixture
    def ssl_valid(self):
        return SslInfo(
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            days_remaining=200,
        )

    @pytest.fixture
    def mocks(self, mocker, active_urls):
        url_repo = mocker.AsyncMock()
        url_repo.get_all_active.return_value = active_urls
        health_repo = mocker.AsyncMock()
        alert_repo = mocker.AsyncMock()
        http_checker = mocker.AsyncMock()
        ssl_checker = mocker.AsyncMock()
        return url_repo, health_repo, alert_repo, http_checker, ssl_checker

    @pytest.fixture
    def use_case(self, mocks):
        url_repo, health_repo, alert_repo, http_checker, ssl_checker = mocks
        return CheckAllUrlsUseCase(
            url_repo=url_repo,
            health_check_repo=health_repo,
            alert_repo=alert_repo,
            http_checker=http_checker,
            ssl_checker=ssl_checker,
        )

    async def test_healthy_urls(self, use_case, mocks, ssl_valid):
        _, _, alert_repo, http_checker, ssl_checker = mocks
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert alerts == []
        alert_repo.save.assert_not_called()

    async def test_unhealthy_url(self, use_case, mocks, ssl_valid):
        _, _, alert_repo, http_checker, ssl_checker = mocks
        http_checker.check.side_effect = [HTTP_503, HTTP_OK]
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.HTTP_DOWN
        alert_repo.save.assert_awaited_once()

    async def test_url_with_timeout(self, use_case, mocks, ssl_valid):
        _, _, alert_repo, http_checker, ssl_checker = mocks
        http_checker.check.side_effect = [TIMEOUT, HTTP_OK]
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.HTTP_DOWN

    async def test_ssl_expiry_alert(self, use_case, mocks):
        _, _, alert_repo, http_checker, ssl_checker = mocks
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = SslInfo(
            expiration_date=datetime(2026, 6, 20, tzinfo=timezone.utc),
            days_remaining=10,
        )

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.SSL_EXPIRY
        assert "10 days" in alerts[0].message

    async def test_non_https_skips_ssl(self, use_case, mocks):
        _, _, alert_repo, http_checker, ssl_checker = mocks
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = None

        alerts = await use_case.execute()
        assert alerts == []
        assert ssl_checker.check.await_count == 1

    async def test_exception_during_check(self, use_case, mocks):
        _, health_repo, alert_repo, http_checker, _ = mocks
        http_checker.check.side_effect = Exception("Unexpected error")

        alerts = await use_case.execute()
        assert alerts == []
        health_repo.save.assert_not_called()
        alert_repo.save.assert_not_called()
