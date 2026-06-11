from datetime import date, datetime, timezone

from healthchecker.domain.models.daily_summary import DailySummary


class TestDailySummaryModel:
    def test_create_summary(self):
        now = datetime.now(timezone.utc)
        s = DailySummary(
            id=None,
            url_id=1,
            summary_date=date(2026, 6, 10),
            checks_count=1440,
            avg_ttfb_ms=120.5,
            min_ttfb_ms=50.0,
            max_ttfb_ms=500.0,
            min_ssl_days_remaining=45,
            healthy_count=1440,
            unhealthy_count=0,
            last_http_status=200,
            last_ssl_expiration_date=now,
            last_checked_at=now,
            created_at=now,
        )
        assert s.url_id == 1
        assert s.summary_date == date(2026, 6, 10)
        assert s.checks_count == 1440
        assert s.avg_ttfb_ms == 120.5
        assert s.healthy_count == 1440
        assert s.min_ssl_days_remaining == 45

    def test_summary_with_partial_failures(self):
        s = DailySummary(
            id=5,
            url_id=2,
            summary_date=date(2026, 6, 9),
            checks_count=100,
            avg_ttfb_ms=None,
            min_ttfb_ms=None,
            max_ttfb_ms=None,
            min_ssl_days_remaining=None,
            healthy_count=80,
            unhealthy_count=20,
            last_http_status=503,
            last_ssl_expiration_date=None,
            last_checked_at=None,
            created_at=None,
        )
        assert s.id == 5
        assert s.healthy_count == 80
        assert s.unhealthy_count == 20
        assert s.avg_ttfb_ms is None
