from datetime import UTC, datetime, timedelta

from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.services.degradation_service import (
    DegradationDetector,
    DegradationReason,
)


def make_check(ttfb, healthy, minutes_ago):
    return HealthCheck(
        id=None,
        url_id=1,
        http_status=200 if healthy else 503,
        ttfb_ms=ttfb,
        ssl_days_remaining=200,
        ssl_expiration_date=datetime(2026, 12, 31, tzinfo=UTC),
        is_healthy=healthy,
        error_message=None if healthy else "Error",
        checked_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
    )


class TestDegradationDetector:
    def test_insufficient_data_not_degraded(self):
        checks = [make_check(100.0, True, m) for m in range(3, 0, -1)]
        status = DegradationDetector().detect(checks)
        assert status.is_degraded is False

    def test_normal_ttfb_not_degraded(self):
        checks = [make_check(100.0, True, m) for m in range(20, 0, -1)]
        status = DegradationDetector().detect(checks)
        assert status.is_degraded is False
        assert status.baseline_ttfb_ms == 100.0

    def test_sustained_ttfb_increase_detected(self):
        checks = [make_check(100.0, True, m) for m in range(20, 0, -1)]
        for idx in range(len(checks) - 5, len(checks)):
            checks[idx] = make_check(5000.0, True, minutes_ago=20 - idx)
        status = DegradationDetector().detect(checks)
        assert status.is_degraded is True
        assert status.reason == DegradationReason.TTFB_INCREASE
        assert status.current_ttfb_ms == 5000.0

    def test_isolated_ttfb_spike_not_degraded(self):
        checks = [make_check(100.0, True, m) for m in range(20, 0, -1)]
        checks[0] = make_check(9000.0, True, minutes_ago=20)
        status = DegradationDetector().detect(checks)
        assert status.is_degraded is False

    def test_ttfb_below_floor_uses_multiplier(self):
        checks = [make_check(50.0, True, m) for m in range(20, 0, -1)]
        for idx in range(len(checks) - 5, len(checks)):
            checks[idx] = make_check(200.0, True, minutes_ago=20 - idx)
        detector = DegradationDetector(ttfb_multiplier=1.5, ttfb_floor_ms=1000.0)
        status = detector.detect(checks)
        assert status.is_degraded is False

    def test_ttfb_above_floor_detected(self):
        checks = [make_check(50.0, True, m) for m in range(20, 0, -1)]
        for idx in range(len(checks) - 5, len(checks)):
            checks[idx] = make_check(2000.0, True, minutes_ago=20 - idx)
        detector = DegradationDetector(ttfb_multiplier=1.5, ttfb_floor_ms=1000.0)
        status = detector.detect(checks)
        assert status.is_degraded is True
        assert status.reason == DegradationReason.TTFB_INCREASE

    def test_intermittent_failures_detected(self):
        checks = [make_check(100.0, True, m) for m in range(20, 0, -1)]
        checks[0] = make_check(None, False, minutes_ago=20)
        checks[1] = make_check(None, False, minutes_ago=19)
        checks[2] = make_check(None, False, minutes_ago=18)
        status = DegradationDetector().detect(checks)
        assert status.is_degraded is True
        assert status.reason == DegradationReason.INTERMITTENT_FAILURES
        assert status.failure_count == 3

    def test_fully_down_not_degraded(self):
        checks = [make_check(100.0, True, m) for m in range(15, 1, -1)]
        checks.append(make_check(None, False, minutes_ago=1))
        checks.append(make_check(None, False, minutes_ago=0))
        status = DegradationDetector().detect(checks)
        assert status.is_degraded is False

    def test_too_many_failures_not_intermittent(self):
        checks = [make_check(100.0, True, m) for m in range(20, 0, -1)]
        for idx in range(15):
            checks[idx] = make_check(None, False, minutes_ago=20 - idx)
        status = DegradationDetector().detect(checks)
        assert status.is_degraded is False

    def test_order_agnostic(self):
        checks = [make_check(100.0, True, m) for m in range(20, 0, -1)]
        for idx in range(len(checks) - 5, len(checks)):
            checks[idx] = make_check(5000.0, True, minutes_ago=20 - idx)
        reversed_checks = list(reversed(checks))
        assert DegradationDetector().detect(checks).is_degraded is True
        assert DegradationDetector().detect(reversed_checks).is_degraded is True
