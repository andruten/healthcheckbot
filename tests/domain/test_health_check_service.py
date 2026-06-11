from datetime import datetime, timezone

from healthchecker.domain.models.alert import AlertType
from healthchecker.domain.services.health_check_service import HealthCheckService


class TestHealthCheckService:
    def test_should_alert_ssl_below_threshold(self):
        assert HealthCheckService.should_alert_ssl(10, 30) is True

    def test_should_alert_ssl_at_threshold(self):
        assert HealthCheckService.should_alert_ssl(30, 30) is True

    def test_should_not_alert_ssl_above_threshold(self):
        assert HealthCheckService.should_alert_ssl(31, 30) is False

    def test_should_not_alert_ssl_none(self):
        assert HealthCheckService.should_alert_ssl(None, 30) is False

    def test_build_ssl_alert_without_expiration(self):
        alert = HealthCheckService.build_ssl_alert(
            url_id=1,
            url_name="Example",
            days_remaining=5,
            threshold_days=30,
        )
        assert alert.url_id == 1
        assert alert.alert_type == AlertType.SSL_EXPIRY
        assert "5 days" in alert.message
        assert "30 days" in alert.message
        assert alert.is_sent is False

    def test_build_ssl_alert_with_expiration(self):
        exp_date = datetime(2026, 7, 15, tzinfo=timezone.utc)
        alert = HealthCheckService.build_ssl_alert(
            url_id=1,
            url_name="Example",
            days_remaining=5,
            threshold_days=30,
            expiration_date=exp_date,
        )
        assert "expires on 2026-07-15" in alert.message

    def test_build_http_down_alert_with_status(self):
        alert = HealthCheckService.build_http_down_alert(1, "Example", 503, None)
        assert alert.alert_type == AlertType.HTTP_DOWN
        assert "503" in alert.message

    def test_build_http_down_alert_with_error(self):
        alert = HealthCheckService.build_http_down_alert(
            1,
            "Example",
            None,
            "Connection refused",
        )
        assert alert.alert_type == AlertType.HTTP_DOWN
        assert "Connection refused" in alert.message
