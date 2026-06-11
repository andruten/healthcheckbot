from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HealthCheck:
    id: int | None
    url_id: int
    http_status: int | None
    ttfb_ms: float | None
    ssl_expiration_date: datetime | None
    ssl_days_remaining: int | None
    is_healthy: bool
    error_message: str | None
    checked_at: datetime
