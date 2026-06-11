from datetime import date

from healthchecker.domain.models.daily_summary import DailySummary
from healthchecker.domain.repositories.daily_summary_repository import (
    DailySummaryRepository as DailySummaryRepositoryInterface,
)
from healthchecker.infrastructure.persistence.tortoise_models import DailySummaryModel


class TortoiseDailySummaryRepository(DailySummaryRepositoryInterface):
    async def save(self, summary: DailySummary) -> DailySummary:
        existing = await self.get_by_url_id_and_date(
            summary.url_id, summary.summary_date
        )
        if existing:
            await DailySummaryModel.filter(id=existing.id).update(
                checks_count=summary.checks_count,
                avg_ttfb_ms=summary.avg_ttfb_ms,
                min_ttfb_ms=summary.min_ttfb_ms,
                max_ttfb_ms=summary.max_ttfb_ms,
                min_ssl_days_remaining=summary.min_ssl_days_remaining,
                healthy_count=summary.healthy_count,
                unhealthy_count=summary.unhealthy_count,
                last_http_status=summary.last_http_status,
                last_ssl_expiration_date=summary.last_ssl_expiration_date,
                last_checked_at=summary.last_checked_at,
            )
            summary.id = existing.id
            return summary

        row = await DailySummaryModel.create(
            url_id=summary.url_id,
            date=summary.summary_date,
            checks_count=summary.checks_count,
            avg_ttfb_ms=summary.avg_ttfb_ms,
            min_ttfb_ms=summary.min_ttfb_ms,
            max_ttfb_ms=summary.max_ttfb_ms,
            min_ssl_days_remaining=summary.min_ssl_days_remaining,
            healthy_count=summary.healthy_count,
            unhealthy_count=summary.unhealthy_count,
            last_http_status=summary.last_http_status,
            last_ssl_expiration_date=summary.last_ssl_expiration_date,
            last_checked_at=summary.last_checked_at,
        )
        summary.id = row.id
        return summary

    async def get_by_url_id_and_date(
        self, url_id: int, summary_date: date
    ) -> DailySummary | None:
        row = await DailySummaryModel.get_or_none(url_id=url_id, date=summary_date)
        return self._to_domain(row) if row else None

    async def get_by_url_id(
        self, url_id: int, limit: int = 10, offset: int = 0
    ) -> list[DailySummary]:
        rows = (
            await DailySummaryModel.filter(url_id=url_id)
            .order_by("-date")
            .limit(limit)
            .offset(offset)
        )
        return [self._to_domain(r) for r in rows]

    async def exists_for_date(self, url_id: int, summary_date: date) -> bool:
        return await DailySummaryModel.filter(url_id=url_id, date=summary_date).exists()

    @staticmethod
    def _to_domain(row: DailySummaryModel) -> DailySummary:
        return DailySummary(
            id=row.id,
            url_id=row.url_id,
            summary_date=row.date,
            checks_count=row.checks_count,
            avg_ttfb_ms=float(row.avg_ttfb_ms) if row.avg_ttfb_ms is not None else None,
            min_ttfb_ms=float(row.min_ttfb_ms) if row.min_ttfb_ms is not None else None,
            max_ttfb_ms=float(row.max_ttfb_ms) if row.max_ttfb_ms is not None else None,
            min_ssl_days_remaining=row.min_ssl_days_remaining,
            healthy_count=row.healthy_count,
            unhealthy_count=row.unhealthy_count,
            last_http_status=row.last_http_status,
            last_ssl_expiration_date=row.last_ssl_expiration_date,
            last_checked_at=row.last_checked_at,
            created_at=row.created_at,
        )
