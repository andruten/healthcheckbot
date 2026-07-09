from datetime import datetime, timezone

import pytest

from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.interfaces.telegram.handlers.list_urls import ListUrlsHandler


class TestListUrlsHandler:
    def test_format_status_healthy(self):
        check = HealthCheck(
            id=1,
            url_id=1,
            http_status=200,
            ttfb_ms=120.0,
            ssl_days_remaining=45,
            ssl_expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )
        result = ListUrlsHandler._format_status(check, alert_before_days=30)
        assert "✅" in result
        assert "HTTP 200" in result
        assert "120ms" in result
        assert "SSL: 45d" in result
        assert "Expires: 2026-12-31" in result

    def test_format_status_ssl_expiring_soon(self):
        check = HealthCheck(
            id=2,
            url_id=1,
            http_status=200,
            ttfb_ms=100.0,
            ssl_days_remaining=10,
            ssl_expiration_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )
        result = ListUrlsHandler._format_status(check, alert_before_days=30)
        assert "⚠️" in result
        assert "SSL: 10d" in result

    def test_format_status_ssl_expiring_exactly_at_threshold(self):
        check = HealthCheck(
            id=3,
            url_id=1,
            http_status=200,
            ttfb_ms=100.0,
            ssl_days_remaining=30,
            ssl_expiration_date=datetime(2026, 7, 19, tzinfo=timezone.utc),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )
        result = ListUrlsHandler._format_status(check, alert_before_days=30)
        assert "⚠️" in result

    def test_format_status_unhealthy(self):
        check = HealthCheck(
            id=4,
            url_id=1,
            http_status=503,
            ttfb_ms=None,
            ssl_days_remaining=45,
            ssl_expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            is_healthy=False,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )
        result = ListUrlsHandler._format_status(check, alert_before_days=30)
        assert "❌" in result
        assert "HTTP 503" in result

    def test_format_status_with_error(self):
        check = HealthCheck(
            id=5,
            url_id=1,
            http_status=None,
            ttfb_ms=None,
            ssl_days_remaining=None,
            ssl_expiration_date=None,
            is_healthy=False,
            error_message="Connection timeout",
            checked_at=datetime.now(timezone.utc),
        )
        result = ListUrlsHandler._format_status(check, alert_before_days=30)
        assert "❌ Error: Connection timeout" == result

    def test_format_status_no_ssl_info(self):
        check = HealthCheck(
            id=6,
            url_id=1,
            http_status=200,
            ttfb_ms=80.0,
            ssl_days_remaining=None,
            ssl_expiration_date=None,
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )
        result = ListUrlsHandler._format_status(check, alert_before_days=30)
        assert "✅" in result
        assert "SSL" not in result

    def test_format_status_no_ttfb(self):
        check = HealthCheck(
            id=7,
            url_id=1,
            http_status=204,
            ttfb_ms=None,
            ssl_days_remaining=60,
            ssl_expiration_date=None,
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )
        result = ListUrlsHandler._format_status(check, alert_before_days=30)
        assert "✅" in result
        assert "HTTP 204" in result
        assert "ms" not in result

    @pytest.fixture
    def mock_check(self):
        return HealthCheck(
            id=8,
            url_id=1,
            http_status=200,
            ttfb_ms=90.0,
            ssl_days_remaining=45,
            ssl_expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )

    async def test_handler_no_urls(self, mocker):
        manage_urls = mocker.AsyncMock()
        manage_urls.list_all.return_value = []
        get_results = mocker.AsyncMock()
        handler = ListUrlsHandler(manage_urls, get_results)

        update = mocker.AsyncMock()
        context = mocker.AsyncMock()
        await handler.handle(update, context)

        update.message.reply_text.assert_awaited_once_with(
            "No URLs are being monitored. Use /add to add one."
        )

    async def test_handler_with_urls(self, mocker, mock_check):
        url = mocker.Mock()
        url.id = 1
        url.name = "Example"
        url.url = "https://example.com"
        url.alert_before_days = 30

        manage_urls = mocker.AsyncMock()
        manage_urls.list_all.return_value = [url]
        get_results = mocker.AsyncMock()
        get_results.get_latest.return_value = mock_check
        handler = ListUrlsHandler(manage_urls, get_results)

        update = mocker.AsyncMock()
        context = mocker.AsyncMock()
        await handler.handle(update, context)

        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "Example" in text
        assert "https://example.com" in text
        assert "✅" in text

    async def test_handler_with_url_not_checked_yet(self, mocker):
        url = mocker.Mock()
        url.id = 1
        url.name = "Example"
        url.url = "https://example.com"
        url.alert_before_days = 30

        manage_urls = mocker.AsyncMock()
        manage_urls.list_all.return_value = [url]
        get_results = mocker.AsyncMock()
        get_results.get_latest.return_value = None
        handler = ListUrlsHandler(manage_urls, get_results)

        update = mocker.AsyncMock()
        context = mocker.AsyncMock()
        await handler.handle(update, context)

        text = update.message.reply_text.call_args[0][0]
        assert "⏳" in text

    async def test_handler_ssl_expiring_icon(self, mocker):
        url = mocker.Mock()
        url.id = 1
        url.name = "Example"
        url.url = "https://example.com"
        url.alert_before_days = 30

        check = HealthCheck(
            id=9,
            url_id=1,
            http_status=200,
            ttfb_ms=90.0,
            ssl_days_remaining=10,
            ssl_expiration_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
            is_healthy=True,
            error_message=None,
            checked_at=datetime.now(timezone.utc),
        )

        manage_urls = mocker.AsyncMock()
        manage_urls.list_all.return_value = [url]
        get_results = mocker.AsyncMock()
        get_results.get_latest.return_value = check
        handler = ListUrlsHandler(manage_urls, get_results)

        update = mocker.AsyncMock()
        context = mocker.AsyncMock()
        await handler.handle(update, context)

        text = update.message.reply_text.call_args[0][0]
        assert "⚠️" in text
