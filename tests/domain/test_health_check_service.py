from datetime import UTC, datetime

from healthchecker.domain.models.alert import AlertType
from healthchecker.domain.services.degradation_service import (
    DegradationReason,
    DegradationStatus,
)
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
        exp_date = datetime(2026, 7, 15, tzinfo=UTC)
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

    def test_build_http_down_alert_escapes_error_markdown(self):
        error = (
            "[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1082)"
        )
        alert = HealthCheckService.build_http_down_alert(1, "Example", None, error)
        assert "\\[SSL: TLSV1\\_ALERT\\_INTERNAL\\_ERROR]" in alert.message
        assert "\\_ssl.c:1082" in alert.message

    def test_build_http_down_alert_escapes_url_name(self):
        alert = HealthCheckService.build_http_down_alert(1, "My*Service", 503, None)
        assert "*My\\*Service* is DOWN." in alert.message

    def test_build_ssl_alert_escapes_url_name(self):
        alert = HealthCheckService.build_ssl_alert(
            url_id=1,
            url_name="My*Service",
            days_remaining=5,
            threshold_days=30,
        )
        assert "*My\\*Service*" in alert.message

    def test_build_http_up_alert_escapes_url_name(self):
        alert = HealthCheckService.build_http_up_alert(1, "My*Service", 200, 100.0)
        assert "*My\\*Service*" in alert.message

    def test_build_degradation_start_ttfb_increase(self):
        status = DegradationStatus(
            is_degraded=True,
            reason=DegradationReason.TTFB_INCREASE,
            baseline_ttfb_ms=100.0,
            current_ttfb_ms=1500.0,
        )
        alert = HealthCheckService.build_degradation_start_alert(1, "Example", status)
        assert alert.alert_type == AlertType.DEGRADATION_START
        assert "TTFB up from 100ms to 1500ms" in alert.message

    def test_build_degradation_start_intermittent_failures(self):
        status = DegradationStatus(
            is_degraded=True,
            reason=DegradationReason.INTERMITTENT_FAILURES,
            failure_count=3,
            total_checks=20,
        )
        alert = HealthCheckService.build_degradation_start_alert(1, "Example", status)
        assert "3/20 recent checks failing" in alert.message

    def test_build_degradation_start_escapes_url_name(self):
        status = DegradationStatus(
            is_degraded=True,
            reason=DegradationReason.TTFB_INCREASE,
            baseline_ttfb_ms=100.0,
            current_ttfb_ms=1500.0,
        )
        alert = HealthCheckService.build_degradation_start_alert(
            1, "My*Service", status
        )
        assert "*My\\*Service* is degrading" in alert.message

    def test_build_degradation_recover_alert(self):
        status = DegradationStatus(is_degraded=False, current_ttfb_ms=110.0)
        alert = HealthCheckService.build_degradation_recover_alert(1, "Example", status)
        assert alert.alert_type == AlertType.DEGRADATION_RECOVER
        assert "performance back to normal" in alert.message
        assert "TTFB 110ms" in alert.message

    def test_build_degradation_recover_alert_escapes_url_name(self):
        status = DegradationStatus(is_degraded=False)
        alert = HealthCheckService.build_degradation_recover_alert(
            1, "My*Service", status
        )
        assert "*My\\*Service*" in alert.message
