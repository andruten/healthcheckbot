from datetime import UTC, datetime, timedelta

from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.services.stats_service import HealthCheckStatsService


def _check(
    checked_at: datetime,
    is_healthy: bool = True,
    ttfb_ms: float | None = 100.0,
    ssl_days_remaining: int | None = 45,
):
    return HealthCheck(
        id=None,
        url_id=1,
        http_status=200 if is_healthy else 500,
        ttfb_ms=ttfb_ms,
        ssl_expiration_date=None,
        ssl_days_remaining=ssl_days_remaining,
        is_healthy=is_healthy,
        error_message=None,
        checked_at=checked_at,
    )


class TestHealthCheckStatsService:
    def setup_method(self):
        self.service = HealthCheckStatsService()
        self.base = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)

    def test_empty(self):
        stats = self.service.compute([])
        assert stats.total_checks == 0
        assert stats.uptime_pct is None
        assert stats.ttfb_avg_ms is None
        assert stats.current_streak == 0
        assert stats.window_start is None and stats.window_end is None

    def test_uptime(self):
        checks = [_check(self.base + timedelta(minutes=i)) for i in range(10)]
        checks[3] = _check(self.base + timedelta(minutes=3), is_healthy=False)
        stats = self.service.compute(checks)
        assert stats.total_checks == 10
        assert stats.healthy_count == 9
        assert stats.uptime_pct == 90.0

    def test_unordered_input_is_sorted(self):
        checks = [
            _check(self.base + timedelta(minutes=5)),
            _check(self.base),
        ]
        stats = self.service.compute(checks)
        assert stats.window_start == self.base
        assert stats.window_end == self.base + timedelta(minutes=5)

    def test_ttfb_stats(self):
        values = [100.0, 200.0, 300.0, 400.0]
        checks = [
            _check(self.base + timedelta(minutes=i), ttfb_ms=v)
            for i, v in enumerate(values)
        ]
        stats = self.service.compute(checks)
        assert stats.ttfb_samples == 4
        assert stats.ttfb_avg_ms == 250.0
        assert stats.ttfb_min_ms == 100.0
        assert stats.ttfb_max_ms == 400.0
        assert 300.0 <= stats.ttfb_p95_ms <= 400.0

    def test_ttfb_single_sample(self):
        checks = [_check(self.base, ttfb_ms=120.0)]
        stats = self.service.compute(checks)
        assert stats.ttfb_p95_ms == 120.0

    def test_ttfb_none_everywhere(self):
        checks = [
            _check(self.base + timedelta(minutes=i), ttfb_ms=None) for i in range(3)
        ]
        stats = self.service.compute(checks)
        assert stats.ttfb_samples == 0
        assert stats.ttfb_avg_ms is None
        assert stats.ttfb_p95_ms is None

    def test_streak_ok(self):
        checks = [_check(self.base + timedelta(minutes=i)) for i in range(5)]
        checks[2] = _check(self.base + timedelta(minutes=2), is_healthy=False)
        stats = self.service.compute(checks)
        assert stats.current_streak == 2

    def test_streak_failing(self):
        checks = [_check(self.base + timedelta(minutes=i)) for i in range(5)]
        for i in (3, 4):
            checks[i] = _check(self.base + timedelta(minutes=i), is_healthy=False)
        stats = self.service.compute(checks)
        assert stats.current_streak == -2

    def test_last_failure_at(self):
        checks = [_check(self.base + timedelta(minutes=i)) for i in range(5)]
        fail_time = self.base + timedelta(minutes=1)
        checks[1] = _check(fail_time, is_healthy=False)
        stats = self.service.compute(checks)
        assert stats.last_failure_at == fail_time

    def test_last_failure_at_none_when_all_healthy(self):
        checks = [_check(self.base + timedelta(minutes=i)) for i in range(3)]
        stats = self.service.compute(checks)
        assert stats.last_failure_at is None

    def test_min_ssl_days(self):
        checks = [
            _check(self.base + timedelta(minutes=i), ssl_days_remaining=45 - i)
            for i in range(3)
        ]
        stats = self.service.compute(checks)
        assert stats.min_ssl_days_remaining == 43

    def test_ssl_none_everywhere(self):
        checks = [
            _check(self.base + timedelta(minutes=i), ssl_days_remaining=None)
            for i in range(3)
        ]
        stats = self.service.compute(checks)
        assert stats.min_ssl_days_remaining is None
