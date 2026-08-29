from datetime import UTC, datetime

from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.services.degradation_service import (
    DegradationReason,
    DegradationStatus,
)
from healthchecker.interfaces.telegram.handlers.stats import StatsHandler


class TestStatsHandler:
    def test_format_degradation_ttfb_increase(self):
        status = DegradationStatus(
            is_degraded=True,
            reason=DegradationReason.TTFB_INCREASE,
            baseline_ttfb_ms=100.0,
            current_ttfb_ms=1500.0,
        )
        result = StatsHandler._format_degradation(status)
        assert "TTFB up from 100ms to 1500ms" in result

    def test_format_degradation_intermittent_failures(self):
        status = DegradationStatus(
            is_degraded=True,
            reason=DegradationReason.INTERMITTENT_FAILURES,
            failure_count=3,
            total_checks=20,
        )
        result = StatsHandler._format_degradation(status)
        assert "3/20 checks failing" in result

    def test_format_latest_escapes_markdown_error_message(self):
        check = HealthCheck(
            id=1,
            url_id=1,
            http_status=None,
            ttfb_ms=None,
            ssl_days_remaining=None,
            ssl_expiration_date=None,
            is_healthy=False,
            error_message=(
                "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: "
                "self-signed certificate (_ssl.c:1082)"
            ),
            checked_at=datetime(2026, 7, 13, 21, 0, tzinfo=UTC),
        )

        result = StatsHandler._format_latest(check)

        assert "\\_ssl.c" in result
