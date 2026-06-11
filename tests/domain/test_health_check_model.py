from datetime import datetime, timezone

from healthchecker.domain.models.health_check import HealthCheck


class TestHealthCheckModel:
    def test_create_health_check(self):
        now = datetime.now(timezone.utc)
        check = HealthCheck(
            id=None,
            url_id=1,
            http_status=200,
            ttfb_ms=120.5,
            ssl_expiration_date=now,
            ssl_days_remaining=45,
            is_healthy=True,
            error_message=None,
            checked_at=now,
        )
        assert check.id is None
        assert check.url_id == 1
        assert check.http_status == 200
        assert check.ttfb_ms == 120.5
        assert check.ssl_days_remaining == 45
        assert check.is_healthy is True
        assert check.error_message is None

    def test_health_check_is_frozen(self):
        now = datetime.now(timezone.utc)
        check = HealthCheck(
            id=1,
            url_id=1,
            http_status=503,
            ttfb_ms=None,
            ssl_expiration_date=None,
            ssl_days_remaining=None,
            is_healthy=False,
            error_message="Timeout",
            checked_at=now,
        )
        import pytest

        with pytest.raises(AttributeError):
            check.is_healthy = True

    def test_health_check_with_error(self):
        now = datetime.now(timezone.utc)
        check = HealthCheck(
            id=2,
            url_id=1,
            http_status=None,
            ttfb_ms=None,
            ssl_expiration_date=None,
            ssl_days_remaining=None,
            is_healthy=False,
            error_message="Connection refused",
            checked_at=now,
        )
        assert check.http_status is None
        assert check.ttfb_ms is None
        assert check.error_message == "Connection refused"

    def test_health_check_equality(self):
        now = datetime.now(timezone.utc)
        a = HealthCheck(1, 1, 200, 10.0, now, 30, True, None, now)
        b = HealthCheck(1, 1, 200, 10.0, now, 30, True, None, now)
        assert a == b
