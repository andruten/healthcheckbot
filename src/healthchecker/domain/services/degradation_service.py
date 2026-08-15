from dataclasses import dataclass
from enum import Enum
from statistics import median

from healthchecker.domain.models.health_check import HealthCheck


class DegradationReason(str, Enum):
    TTFB_INCREASE = "ttfb_increase"
    INTERMITTENT_FAILURES = "intermittent_failures"


@dataclass(frozen=True)
class DegradationStatus:
    is_degraded: bool
    reason: DegradationReason | None = None
    baseline_ttfb_ms: float | None = None
    current_ttfb_ms: float | None = None
    failure_count: int = 0
    total_checks: int = 0


class DegradationDetector:
    def __init__(
        self,
        window_size: int = 20,
        trend_size: int = 5,
        min_checks: int = 10,
        min_ttfb_samples: int = 5,
        ttfb_multiplier: float = 1.5,
        ttfb_floor_ms: float = 1000.0,
        failure_ratio_max: float = 0.5,
        min_failures: int = 3,
    ) -> None:
        self._window_size = window_size
        self._trend_size = trend_size
        self._min_checks = min_checks
        self._min_ttfb_samples = min_ttfb_samples
        self._ttfb_multiplier = ttfb_multiplier
        self._ttfb_floor_ms = ttfb_floor_ms
        self._failure_ratio_max = failure_ratio_max
        self._min_failures = min_failures

    def detect(self, checks: list[HealthCheck]) -> DegradationStatus:
        ordered = sorted(checks, key=lambda c: c.checked_at)
        window = ordered[-self._window_size :]
        failure_count = sum(1 for c in window if not c.is_healthy)

        if len(window) < self._min_checks:
            return DegradationStatus(
                is_degraded=False,
                failure_count=failure_count,
                total_checks=len(window),
            )

        if not window[-1].is_healthy:
            return DegradationStatus(
                is_degraded=False,
                failure_count=failure_count,
                total_checks=len(window),
            )

        ttfb_degraded, baseline, current = self._check_ttfb(window)
        failures_degraded = self._check_failures(window, failure_count)

        reason = None
        if ttfb_degraded:
            reason = DegradationReason.TTFB_INCREASE
        elif failures_degraded:
            reason = DegradationReason.INTERMITTENT_FAILURES

        return DegradationStatus(
            is_degraded=reason is not None,
            reason=reason,
            baseline_ttfb_ms=baseline,
            current_ttfb_ms=current,
            failure_count=failure_count,
            total_checks=len(window),
        )

    def _check_ttfb(
        self, window: list[HealthCheck]
    ) -> tuple[bool, float | None, float | None]:
        values = [c.ttfb_ms for c in window if c.is_healthy and c.ttfb_ms is not None]
        if len(values) < self._min_ttfb_samples:
            return False, None, None

        baseline = median(values)
        trend = values[-self._trend_size :]
        if not trend:
            return False, baseline, None

        current = median(trend)
        threshold = max(baseline * self._ttfb_multiplier, self._ttfb_floor_ms)
        return current >= threshold, baseline, current

    def _check_failures(self, window: list[HealthCheck], failure_count: int) -> bool:
        if failure_count < self._min_failures:
            return False
        ratio = failure_count / len(window)
        return ratio <= self._failure_ratio_max
