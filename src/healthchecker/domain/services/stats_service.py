from statistics import quantiles

from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.models.health_check_stats import HealthCheckStats


class HealthCheckStatsService:
    def compute(self, checks: list[HealthCheck]) -> HealthCheckStats:
        ordered = sorted(checks, key=lambda c: c.checked_at)
        total = len(ordered)
        healthy = sum(1 for c in ordered if c.is_healthy)
        uptime_pct = (healthy / total * 100.0) if total else None

        ttfb_values = [c.ttfb_ms for c in ordered if c.ttfb_ms is not None]
        ttfb_samples = len(ttfb_values)
        if ttfb_samples:
            avg = sum(ttfb_values) / ttfb_samples
            if ttfb_samples >= 2:
                p95 = quantiles(ttfb_values, n=100, method="inclusive")[94]
            else:
                p95 = ttfb_values[0]
            ttfb_min = min(ttfb_values)
            ttfb_max = max(ttfb_values)
        else:
            avg = p95 = ttfb_min = ttfb_max = None

        streak = 0
        for c in reversed(ordered):
            if c.is_healthy:
                streak += 1
            else:
                break
        if streak == 0:
            failures = 0
            for c in reversed(ordered):
                if not c.is_healthy:
                    failures += 1
                else:
                    break
            streak = -failures

        last_failure_at = None
        for c in reversed(ordered):
            if not c.is_healthy:
                last_failure_at = c.checked_at
                break

        ssl_days = [
            c.ssl_days_remaining for c in ordered if c.ssl_days_remaining is not None
        ]
        min_ssl_days = min(ssl_days) if ssl_days else None
        last_ssl_expiration = None
        for c in reversed(ordered):
            if c.ssl_expiration_date:
                last_ssl_expiration = c.ssl_expiration_date
                break

        return HealthCheckStats(
            total_checks=total,
            healthy_count=healthy,
            uptime_pct=uptime_pct,
            ttfb_avg_ms=avg,
            ttfb_p95_ms=p95,
            ttfb_min_ms=ttfb_min,
            ttfb_max_ms=ttfb_max,
            ttfb_samples=ttfb_samples,
            current_streak=streak,
            last_failure_at=last_failure_at,
            min_ssl_days_remaining=min_ssl_days,
            last_ssl_expiration_date=last_ssl_expiration,
            window_start=ordered[0].checked_at if ordered else None,
            window_end=ordered[-1].checked_at if ordered else None,
        )
