import asyncio
import logging
from datetime import UTC, datetime, timedelta

import pytest
from tortoise.exceptions import IntegrityError

from healthchecker.application.use_cases.check_all_urls import CheckAllUrlsUseCase
from healthchecker.domain.models.alert import AlertType
from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.models.url import Url
from healthchecker.infrastructure.checker.http_checker import HttpCheckResult
from healthchecker.infrastructure.checker.ssl_checker import SslInfo

HTTP_OK = HttpCheckResult(status_code=200, ttfb_ms=100.0, error=None)
HTTP_503 = HttpCheckResult(status_code=503, ttfb_ms=50.0, error=None)
TIMEOUT = HttpCheckResult(status_code=None, ttfb_ms=None, error="Timeout")


def make_check(ttfb, healthy, minutes_ago, url_id=1):
    return HealthCheck(
        id=None,
        url_id=url_id,
        http_status=200 if healthy else 503,
        ttfb_ms=ttfb,
        ssl_days_remaining=200,
        ssl_expiration_date=datetime(2026, 12, 31, tzinfo=UTC),
        is_healthy=healthy,
        error_message=None if healthy else "Error",
        checked_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
    )


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
            expiration_date=datetime(2026, 12, 31, tzinfo=UTC),
            days_remaining=200,
        )

    @pytest.fixture
    def mocks(self, mocker, active_urls):
        url_repo = mocker.AsyncMock()
        url_repo.get_all_active.return_value = active_urls
        health_repo = mocker.AsyncMock()
        health_repo.get_by_url_id.return_value = []
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
        _, _, _alert_repo, http_checker, ssl_checker = mocks
        http_checker.check.side_effect = lambda url: (
            TIMEOUT if "example.com" in url else HTTP_OK
        )
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.HTTP_DOWN

    async def test_url_deleted_mid_check_logs_warning_and_continues(
        self, use_case, mocks, ssl_valid, caplog
    ):
        _, health_repo, alert_repo, http_checker, ssl_checker = mocks

        async def save_fail_for_deleted(check):
            if check.url_id == 1:
                raise IntegrityError("1452 FK constraint fails")
            return check

        health_repo.save.side_effect = save_fail_for_deleted
        http_checker.check.side_effect = lambda url: (
            HTTP_OK if "example.com" in url else HTTP_503
        )
        ssl_checker.check.return_value = ssl_valid

        with caplog.at_level(logging.WARNING):
            alerts = await use_case.execute()

        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.HTTP_DOWN
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("https://example.com" in r.getMessage() for r in warnings)
        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
        alert_repo.save.assert_awaited_once()

    async def test_ssl_expiry_alert(self, use_case, mocks):
        _, _, _alert_repo, http_checker, ssl_checker = mocks
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = SslInfo(
            expiration_date=datetime(2026, 6, 20, tzinfo=UTC),
            days_remaining=10,
        )

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.SSL_EXPIRY
        assert "10 days" in alerts[0].message

    async def test_non_https_skips_ssl(self, use_case, mocks):
        _, _, _alert_repo, http_checker, ssl_checker = mocks
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
        previous = make_check(None, False, minutes_ago=1)
        health_repo.get_by_url_id.return_value = [previous]
        http_checker.check.return_value = HTTP_503
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert alerts == []
        alert_repo.save.assert_not_called()

    async def test_alert_when_transition_to_unhealthy(self, use_case, mocks, ssl_valid):
        _, health_repo, _alert_repo, http_checker, ssl_checker = mocks
        previous = make_check(100.0, True, minutes_ago=1)
        health_repo.get_by_url_id.side_effect = lambda url_id, limit: (
            [previous] if url_id == 1 else []
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
        previous = HealthCheck(
            id=97,
            url_id=1,
            http_status=200,
            ttfb_ms=100.0,
            ssl_days_remaining=10,
            ssl_expiration_date=datetime(2026, 6, 20, tzinfo=UTC),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(UTC),
        )
        health_repo.get_by_url_id.return_value = [previous]
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = SslInfo(
            expiration_date=datetime(2026, 6, 20, tzinfo=UTC),
            days_remaining=9,
        )

        alerts = await use_case.execute()
        assert alerts == []

    async def test_ssl_alert_when_newly_expired(self, use_case, mocks):
        _, health_repo, _alert_repo, http_checker, ssl_checker = mocks
        previous = HealthCheck(
            id=96,
            url_id=1,
            http_status=200,
            ttfb_ms=100.0,
            ssl_days_remaining=31,
            ssl_expiration_date=datetime(2026, 7, 18, tzinfo=UTC),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(UTC),
        )
        health_repo.get_by_url_id.return_value = [previous]
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = SslInfo(
            expiration_date=datetime(2026, 6, 20, tzinfo=UTC),
            days_remaining=10,
        )

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.SSL_EXPIRY

    async def test_alert_when_transition_to_healthy(self, use_case, mocks, ssl_valid):
        _, health_repo, _alert_repo, http_checker, ssl_checker = mocks
        previous = make_check(None, False, minutes_ago=1)
        health_repo.get_by_url_id.side_effect = lambda url_id, limit: (
            [previous] if url_id == 1 else []
        )
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.HTTP_UP
        assert "UP again" in alerts[0].message

    async def test_no_alert_when_already_healthy(self, use_case, mocks, ssl_valid):
        _, health_repo, alert_repo, http_checker, ssl_checker = mocks
        previous = make_check(100.0, True, minutes_ago=1)
        health_repo.get_by_url_id.return_value = [previous]
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert alerts == []
        alert_repo.save.assert_not_called()

    async def test_degradation_start_on_ttfb_increase(self, use_case, mocks, ssl_valid):
        _, health_repo, _alert_repo, http_checker, ssl_checker = mocks
        history = [make_check(100.0, True, minutes_ago=m) for m in range(12, 0, -1)]
        history[10] = make_check(5000.0, True, minutes_ago=2)
        history[11] = make_check(5000.0, True, minutes_ago=1)
        health_repo.get_by_url_id.return_value = history
        http_checker.check.return_value = HttpCheckResult(
            status_code=200, ttfb_ms=5000.0, error=None
        )
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert any(a.alert_type == AlertType.DEGRADATION_START for a in alerts)
        start = next(a for a in alerts if a.alert_type == AlertType.DEGRADATION_START)
        assert "5000ms" in start.message

    async def test_degradation_recover_alert(self, use_case, mocks, ssl_valid):
        _, health_repo, _alert_repo, http_checker, ssl_checker = mocks
        history = [make_check(100.0, True, minutes_ago=m) for m in range(15, 0, -1)]
        history[10] = make_check(5000.0, True, minutes_ago=5)
        history[12] = make_check(5000.0, True, minutes_ago=3)
        history[14] = make_check(5000.0, True, minutes_ago=1)
        health_repo.get_by_url_id.return_value = history
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert any(a.alert_type == AlertType.DEGRADATION_RECOVER for a in alerts)

    async def test_degradation_start_on_intermittent_failures(
        self, use_case, mocks, ssl_valid
    ):
        _, health_repo, _alert_repo, http_checker, ssl_checker = mocks
        history = [make_check(100.0, True, minutes_ago=m) for m in range(15, 0, -1)]
        history[12] = make_check(None, False, minutes_ago=3)
        history[13] = make_check(None, False, minutes_ago=2)
        history[14] = make_check(None, False, minutes_ago=1)
        health_repo.get_by_url_id.return_value = history
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = ssl_valid

        alerts = await use_case.execute()
        assert any(a.alert_type == AlertType.DEGRADATION_START for a in alerts)

    async def test_no_degradation_alert_when_disabled(self, mocks, ssl_valid):
        url_repo, health_repo, alert_repo, http_checker, ssl_checker = mocks
        history = [make_check(100.0, True, minutes_ago=m) for m in range(12, 0, -1)]
        history[10] = make_check(5000.0, True, minutes_ago=2)
        history[11] = make_check(5000.0, True, minutes_ago=1)
        health_repo.get_by_url_id.return_value = history
        http_checker.check.return_value = HttpCheckResult(
            status_code=200, ttfb_ms=5000.0, error=None
        )
        ssl_checker.check.return_value = ssl_valid
        use_case = CheckAllUrlsUseCase(
            url_repo=url_repo,
            health_check_repo=health_repo,
            alert_repo=alert_repo,
            http_checker=http_checker,
            ssl_checker=ssl_checker,
            degradation_enabled=False,
        )

        alerts = await use_case.execute()
        assert all(a.alert_type != AlertType.DEGRADATION_START for a in alerts)

    async def test_concurrent_execute_does_not_duplicate_alerts(
        self, use_case, mocks, ssl_valid
    ):
        _, health_repo, alert_repo, http_checker, ssl_checker = mocks
        http_checker.check.return_value = HTTP_503
        ssl_checker.check.return_value = ssl_valid
        saved: dict[int, list[HealthCheck]] = {}

        async def fake_save(check):
            saved.setdefault(check.url_id, []).append(check)

        def fake_history(url_id, limit=None):
            return list(reversed(saved.get(url_id, [])))

        health_repo.save.side_effect = fake_save
        health_repo.get_by_url_id.side_effect = fake_history

        first, second = await asyncio.gather(use_case.execute(), use_case.execute())

        assert len(first) == 2
        assert all(a.alert_type == AlertType.HTTP_DOWN for a in first)
        assert second == []
        assert alert_repo.save.await_count == 2

    async def test_execute_waits_for_in_flight_run(self, use_case, mocks, ssl_valid):
        url_repo, _, _, http_checker, ssl_checker = mocks
        http_checker.check.return_value = HTTP_OK
        ssl_checker.check.return_value = ssl_valid
        first_started = asyncio.Event()
        release_first = asyncio.Event()

        async def blocking_check(url):
            if "example.com" in url:
                first_started.set()
                await release_first.wait()
            return HTTP_OK

        http_checker.check.side_effect = blocking_check

        first = asyncio.create_task(use_case.execute())
        await first_started.wait()

        second = asyncio.create_task(use_case.execute())
        await asyncio.sleep(0.01)
        url_repo.get_all_active.assert_awaited_once()

        release_first.set()
        first_alerts, second_alerts = await asyncio.gather(first, second)

        assert first_alerts == []
        assert second_alerts == []
        assert url_repo.get_all_active.await_count == 2
