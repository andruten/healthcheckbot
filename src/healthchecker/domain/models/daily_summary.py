from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class DailySummary:
    id: int | None
    url_id: int
    summary_date: date
    checks_count: int
    avg_ttfb_ms: float | None
    min_ttfb_ms: float | None
    max_ttfb_ms: float | None
    min_ssl_days_remaining: int | None
    healthy_count: int
    unhealthy_count: int
    last_http_status: int | None
    last_ssl_expiration_date: datetime | None
    last_checked_at: datetime | None
    created_at: datetime | None
