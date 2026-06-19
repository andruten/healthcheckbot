from datetime import datetime, timezone

from healthchecker.domain.models.alert import Alert, AlertType


class HealthCheckService:
    @staticmethod
    def should_alert_ssl(days_remaining: int | None, threshold_days: int) -> bool:
        if days_remaining is None:
            return False
        return days_remaining <= threshold_days

    @staticmethod
    def build_ssl_alert(
        url_id: int,
        url_name: str,
        days_remaining: int,
        threshold_days: int,
        expiration_date: datetime | None = None,
    ) -> Alert:
        date_part = ""
        if expiration_date:
            date_part = f" (expires on {expiration_date.strftime('%Y-%m-%d')})"
        return Alert(
            id=None,
            url_id=url_id,
            alert_type=AlertType.SSL_EXPIRY,
            message=(
                f"⚠️ SSL certificate for *{url_name}* expires in *{days_remaining} days*"
                f"{date_part} "
                f"(threshold: {threshold_days} days)."
            ),
            is_sent=False,
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def build_http_down_alert(
        url_id: int, url_name: str, status: int | None, error: str | None
    ) -> Alert:
        return Alert(
            id=None,
            url_id=url_id,
            alert_type=AlertType.HTTP_DOWN,
            message=(
                f"❌ *{url_name}* is DOWN. "
                + (f"HTTP {status}" if status else f"Error: {error}")
            ),
            is_sent=False,
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def build_http_up_alert(
        url_id: int,
        url_name: str,
        status: int | None,
        ttfb_ms: float | None,
    ) -> Alert:
        ttfb_part = f" | {ttfb_ms:.0f}ms" if ttfb_ms is not None else ""
        return Alert(
            id=None,
            url_id=url_id,
            alert_type=AlertType.HTTP_UP,
            message=(
                f"✅ *{url_name}* is UP again."
                + (f" HTTP {status}{ttfb_part}" if status else "")
            ),
            is_sent=False,
            created_at=datetime.now(timezone.utc),
        )
