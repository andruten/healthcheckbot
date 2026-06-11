import logging
from datetime import date, datetime, timezone

from healthchecker.domain.models.daily_summary import DailySummary
from healthchecker.domain.repositories.health_check_repository import (
    HealthCheckRepository,
)
from healthchecker.domain.repositories.daily_summary_repository import (
    DailySummaryRepository,
)

logger = logging.getLogger(__name__)


class ConsolidateDailySummariesUseCase:
    def __init__(
        self,
        health_check_repo: HealthCheckRepository,
        summary_repo: DailySummaryRepository,
        retention_days: int = 7,
    ):
        self._health_check_repo = health_check_repo
        self._summary_repo = summary_repo
        self._retention_days = retention_days

    async def execute(self) -> int:
        cutoff = date.today()
        pending = await self._health_check_repo.get_dates_needing_consolidation(cutoff)
        if not pending:
            logger.info("No data to consolidate")
            return 0

        consolidated_count = 0
        for url_id, check_date in pending:
            try:
                raw = await self._health_check_repo.get_raw_for_date(url_id, check_date)
                if not raw:
                    continue

                ttfb_values = [c.ttfb_ms for c in raw if c.ttfb_ms is not None]
                ssl_days = [
                    c.ssl_days_remaining
                    for c in raw
                    if c.ssl_days_remaining is not None
                ]

                summary = DailySummary(
                    id=None,
                    url_id=url_id,
                    summary_date=check_date,
                    checks_count=len(raw),
                    avg_ttfb_ms=sum(ttfb_values) / len(ttfb_values)
                    if ttfb_values
                    else None,
                    min_ttfb_ms=min(ttfb_values) if ttfb_values else None,
                    max_ttfb_ms=max(ttfb_values) if ttfb_values else None,
                    min_ssl_days_remaining=min(ssl_days) if ssl_days else None,
                    healthy_count=sum(1 for c in raw if c.is_healthy),
                    unhealthy_count=sum(1 for c in raw if not c.is_healthy),
                    last_http_status=raw[-1].http_status,
                    last_ssl_expiration_date=raw[-1].ssl_expiration_date,
                    last_checked_at=raw[-1].checked_at,
                    created_at=datetime.now(timezone.utc),
                )

                await self._summary_repo.save(summary)
                consolidated_count += 1
                logger.debug(
                    "Consolidated %d checks for url_id=%s on %s",
                    len(raw),
                    url_id,
                    check_date,
                )
            except Exception as e:
                logger.error(
                    "Error consolidating url_id=%s date=%s: %s",
                    url_id,
                    check_date,
                    e,
                    exc_info=True,
                )

        cutoff.replace(day=1)  # keep current month at minimum
        if self._retention_days == 0:
            purged = await self._health_check_repo.purge_older_than(cutoff)
        else:
            from datetime import timedelta

            purge_date = cutoff - timedelta(days=self._retention_days)
            purged = await self._health_check_repo.purge_older_than(purge_date)

        logger.info(
            "Consolidated %d days, purged %d old health checks",
            consolidated_count,
            purged,
        )
        return consolidated_count
