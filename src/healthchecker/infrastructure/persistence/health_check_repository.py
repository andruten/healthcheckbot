from datetime import date, datetime, timezone

from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.repositories.health_check_repository import (
    HealthCheckRepository as HealthCheckRepositoryInterface,
)
from healthchecker.infrastructure.persistence.tortoise_models import (
    HealthCheckModel,
    DailySummaryModel,
)


class TortoiseHealthCheckRepository(HealthCheckRepositoryInterface):
    async def save(self, check: HealthCheck) -> HealthCheck:
        row = await HealthCheckModel.create(
            url_id=check.url_id,
            http_status=check.http_status,
            ttfb_ms=check.ttfb_ms,
            ssl_expiration_date=check.ssl_expiration_date,
            ssl_days_remaining=check.ssl_days_remaining,
            is_healthy=check.is_healthy,
            error_message=check.error_message,
            checked_at=check.checked_at,
        )
        return HealthCheck(
            id=row.id,
            url_id=row.url_id,
            http_status=row.http_status,
            ttfb_ms=float(row.ttfb_ms) if row.ttfb_ms is not None else None,
            ssl_expiration_date=row.ssl_expiration_date,
            ssl_days_remaining=row.ssl_days_remaining,
            is_healthy=row.is_healthy,
            error_message=row.error_message,
            checked_at=row.checked_at,
        )

    async def get_by_url_id(self, url_id: int, limit: int = 10) -> list[HealthCheck]:
        rows = (
            await HealthCheckModel.filter(url_id=url_id)
            .order_by("-checked_at")
            .limit(limit)
        )
        return [self._to_domain(r) for r in rows]

    async def get_latest_by_url_id(self, url_id: int) -> HealthCheck | None:
        row = (
            await HealthCheckModel.filter(url_id=url_id).order_by("-checked_at").first()
        )
        return self._to_domain(row) if row else None

    async def get_dates_needing_consolidation(
        self, cutoff_date: date
    ) -> list[tuple[int, date]]:
        end = datetime(
            cutoff_date.year,
            cutoff_date.month,
            cutoff_date.day,
            23,
            59,
            59,
            tzinfo=timezone.utc,
        )
        raw: set[tuple[int, date]] = set()
        rows = await HealthCheckModel.filter(
            checked_at__lte=end,
        ).values("url_id", "checked_at")
        for r in rows:
            raw.add((r["url_id"], r["checked_at"].date() if r["checked_at"] else None))

        existing: set[tuple[int, date]] = set()
        existing_rows = await DailySummaryModel.filter(
            date__lte=cutoff_date,
        ).values("url_id", "date")
        for r in existing_rows:
            existing.add((r["url_id"], r["date"]))

        pending = sorted(
            [(uid, d) for uid, d in raw if d is not None and (uid, d) not in existing],
            key=lambda x: x[1],
        )
        return pending

    async def get_raw_for_date(
        self, url_id: int, target_date: date
    ) -> list[HealthCheck]:
        start = datetime(
            target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc
        )
        end = datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            23,
            59,
            59,
            tzinfo=timezone.utc,
        )
        rows = await HealthCheckModel.filter(
            url_id=url_id,
            checked_at__gte=start,
            checked_at__lte=end,
        ).order_by("checked_at")
        return [self._to_domain(r) for r in rows]

    async def purge_older_than(self, cutoff_date: date) -> int:
        end = datetime(
            cutoff_date.year,
            cutoff_date.month,
            cutoff_date.day,
            23,
            59,
            59,
            tzinfo=timezone.utc,
        )
        deleted = await HealthCheckModel.filter(checked_at__lte=end).delete()
        return deleted

    @staticmethod
    def _to_domain(row: HealthCheckModel) -> HealthCheck:
        return HealthCheck(
            id=row.id,
            url_id=row.url_id,
            http_status=row.http_status,
            ttfb_ms=float(row.ttfb_ms) if row.ttfb_ms is not None else None,
            ssl_expiration_date=row.ssl_expiration_date,
            ssl_days_remaining=row.ssl_days_remaining,
            is_healthy=row.is_healthy,
            error_message=row.error_message,
            checked_at=row.checked_at,
        )
