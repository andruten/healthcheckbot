from datetime import UTC, datetime

from telegram.helpers import escape_markdown

from healthchecker.domain.models.alert import Alert, AlertType
from healthchecker.domain.services.degradation_service import (
    DegradationReason,
    DegradationStatus,
)


class HealthCheckService:
    @staticmethod
    def _escape(value: str) -> str:
        return escape_markdown(value, version=1)

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
                f"⚠️ SSL certificate for *{HealthCheckService._escape(url_name)}* "
                f"expires in *{days_remaining} days*"
                f"{date_part} "
                f"(threshold: {threshold_days} days)."
            ),
            is_sent=False,
            created_at=datetime.now(UTC),
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
                f"❌ *{HealthCheckService._escape(url_name)}* is DOWN. "
                + (
                    f"HTTP {status}"
                    if status
                    else f"Error: {HealthCheckService._escape(error or '')}"
                )
            ),
            is_sent=False,
            created_at=datetime.now(UTC),
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
                f"✅ *{HealthCheckService._escape(url_name)}* is UP again."
                + (f" HTTP {status}{ttfb_part}" if status else "")
            ),
            is_sent=False,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def build_degradation_start_alert(
        url_id: int, url_name: str, status: DegradationStatus
    ) -> Alert:
        if status.reason == DegradationReason.TTFB_INCREASE:
            detail = (
                f"TTFB up from {status.baseline_ttfb_ms:.0f}ms to "
                f"{status.current_ttfb_ms:.0f}ms"
            )
        elif status.reason == DegradationReason.INTERMITTENT_FAILURES:
            detail = (
                f"{status.failure_count}/{status.total_checks} recent checks failing"
            )
        else:
            detail = "performance degraded"
        return Alert(
            id=None,
            url_id=url_id,
            alert_type=AlertType.DEGRADATION_START,
            message=(
                f"⚠️ *{HealthCheckService._escape(url_name)}* is degrading: {detail}"
            ),
            is_sent=False,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def build_degradation_recover_alert(
        url_id: int, url_name: str, status: DegradationStatus
    ) -> Alert:
        ttfb_part = (
            f" (TTFB {status.current_ttfb_ms:.0f}ms)"
            if status.current_ttfb_ms is not None
            else ""
        )
        return Alert(
            id=None,
            url_id=url_id,
            alert_type=AlertType.DEGRADATION_RECOVER,
            message=(
                f"✅ *{HealthCheckService._escape(url_name)}* "
                f"performance back to normal{ttfb_part}"
            ),
            is_sent=False,
            created_at=datetime.now(UTC),
        )
