from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HealthCheckStats:
    total_checks: int
    healthy_count: int
    uptime_pct: float | None
    ttfb_avg_ms: float | None
    ttfb_p95_ms: float | None
    ttfb_min_ms: float | None
    ttfb_max_ms: float | None
    ttfb_samples: int
    current_streak: int
    last_failure_at: datetime | None
    min_ssl_days_remaining: int | None
    last_ssl_expiration_date: datetime | None
    window_start: datetime | None
    window_end: datetime | None
