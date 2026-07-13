from datetime import datetime, timezone

from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.interfaces.telegram.handlers.results import ResultsHandler


class TestResultsHandler:
    def test_format_raw_check_escapes_markdown_error_message(self):
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
            checked_at=datetime(2026, 7, 13, 21, 0, tzinfo=timezone.utc),
        )

        result = ResultsHandler._format_raw_check(check)

        assert "\\_ssl.c" in result
