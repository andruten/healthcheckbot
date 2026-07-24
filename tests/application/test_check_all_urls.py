from datetime import datetime, timezone

import pytest

from healthchecker.application.use_cases.check_all_urls import CheckAllUrlsUseCase
from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.models.url import Url
from healthchecker.domain.models.alert import AlertType
from healthchecker.infrastructure.checker.http_checker import HttpCheckResult
from healthchecker.infrastructure.checker.ssl_checker import SslInfo


HTTP_OK = HttpCheckResult(status_code=200, ttfb_ms=100.0, error=None)
HTTP_503 = HttpCheckResult(status_code=503, ttfb_ms=50.0, error=None)
TIMEOUT = HttpCheckResult(status_code=None, ttfb_ms=None, error="Timeout")


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
        health_repo.get_latest_by_url_id.return_value = None
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
        http_checker.check.side_effect = lambda url: (
            HTTP_503 if "example.com" in url else HTTP_OK
        )
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.HTTP_DOWN
        alert_repo.save.assert_awaited_once()

    async def test_url_with_timeout(self, use_case, mocks, ssl_valid):
        _, _, alert_repo, http_checker, ssl_checker = mocks
        http_checker.check.side_effect = lambda url: (
            TIMEOUT if "example.com" in url else HTTP_OK
        )
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

    async def test_no_alert_when_already_unhealthy(self, use_case, mocks, ssl_valid):
        _, health_repo, alert_repo, http_checker, ssl_checker = mocks
        health_repo.get_latest_by_url_id.return_value = HealthCheck(
            id=99,
            url_id=1,
            http_status=503,
            ttfb_ms=None,
            ssl_days_remaining=200,
            ssl_expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            is_healthy=False,
            error_message="Previous error",
            checked_at=datetime.now(timezone.utc),
        )
        http_checker.check.return_value = HTTP_503
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert alerts == []
        alert_repo.save.assert_not_called()

    async def test_alert_when_transition_to_unhealthy(self, use_case, mocks, ssl_valid):
        _, health_repo, alert_repo, http_checker, ssl_checker = mocks
        previous = HealthCheck(
            id=98,
            url_id=1,
            http_status=200,
            ttfb_ms=100.0,
            ssl_days_remaining=200,
            ssl_expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )
        health_repo.get_latest_by_url_id.side_effect = lambda url_id: (
            previous if url_id == 1 else None
        )
        http_checker.check.side_effect = lambda url: (
            HTTP_503 if "example.com" in url else HTTP_OK
        )
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.HTTP_DOWN

    async def test_no_ssl_alert_when_already_expired(self, use_case, mocks):
        _, health_repo, _, http_checker, ssl_checker = mocks
        health_repo.get_latest_by_url_id.return_value = HealthCheck(
            id=97,
            url_id=1,
            http_status=200,
            ttfb_ms=100.0,
            ssl_days_remaining=10,
            ssl_expiration_date=datetime(2026, 6, 20, tzinfo=timezone.utc),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = SslInfo(
            expiration_date=datetime(2026, 6, 20, tzinfo=timezone.utc),
            days_remaining=9,
        )

        alerts = await use_case.execute()
        assert alerts == []

    async def test_ssl_alert_when_newly_expired(self, use_case, mocks):
        _, health_repo, alert_repo, http_checker, ssl_checker = mocks
        health_repo.get_latest_by_url_id.return_value = HealthCheck(
            id=96,
            url_id=1,
            http_status=200,
            ttfb_ms=100.0,
            ssl_days_remaining=31,
            ssl_expiration_date=datetime(2026, 7, 18, tzinfo=timezone.utc),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = SslInfo(
            expiration_date=datetime(2026, 6, 20, tzinfo=timezone.utc),
            days_remaining=10,
        )

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.SSL_EXPIRY

    async def test_alert_when_transition_to_healthy(self, use_case, mocks, ssl_valid):
        _, health_repo, alert_repo, http_checker, ssl_checker = mocks
        previous = HealthCheck(
            id=95,
            url_id=1,
            http_status=503,
            ttfb_ms=None,
            ssl_days_remaining=200,
            ssl_expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            is_healthy=False,
            error_message="Previous error",
            checked_at=datetime.now(timezone.utc),
        )
        health_repo.get_latest_by_url_id.side_effect = lambda url_id: (
            previous if url_id == 1 else None
        )
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.HTTP_UP
        assert "UP again" in alerts[0].message

    async def test_no_alert_when_already_healthy(self, use_case, mocks, ssl_valid):
        _, health_repo, alert_repo, http_checker, ssl_checker = mocks
        health_repo.get_latest_by_url_id.return_value = HealthCheck(
            id=94,
            url_id=1,
            http_status=200,
            ttfb_ms=100.0,
            ssl_days_remaining=200,
            ssl_expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert alerts == []
        alert_repo.save.assert_not_called()
