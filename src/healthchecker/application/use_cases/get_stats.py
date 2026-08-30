from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.models.health_check_stats import HealthCheckStats
from healthchecker.domain.repositories.health_check_repository import (
    HealthCheckRepository,
)
from healthchecker.domain.services.degradation_service import (
    DegradationDetector,
    DegradationStatus,
)
from healthchecker.domain.services.stats_service import HealthCheckStatsService
from healthchecker.infrastructure.config import settings


class GetStatsUseCase:
    def __init__(
        self,
        health_check_repo: HealthCheckRepository,
        degradation_detector: DegradationDetector | None = None,
        stats_service: HealthCheckStatsService | None = None,
    ):
        self._health_check_repo = health_check_repo
        self._stats_service = stats_service or HealthCheckStatsService()
        self._degradation_detector = degradation_detector or DegradationDetector(
            window_size=settings.degradation_window_size,
            trend_size=settings.degradation_trend_size,
            min_checks=settings.degradation_min_checks,
            min_ttfb_samples=settings.degradation_min_ttfb_samples,
            ttfb_multiplier=settings.ttfb_degradation_multiplier,
            ttfb_floor_ms=settings.ttfb_warn_floor_ms,
            failure_ratio_max=settings.degradation_failure_ratio,
            min_failures=settings.degradation_min_failures,
        )

    async def get_latest(self, url_id: int):
        return await self._health_check_repo.get_latest_by_url_id(url_id)

    async def get_latest_map(self, url_ids: Sequence[int]) -> dict[int, HealthCheck]:
        return await self._health_check_repo.get_latest_by_url_ids(url_ids)

    async def get_stats(self, url_id: int, days: int | None = None) -> HealthCheckStats:
        period = days if days is not None else settings.stats_default_days
        since = datetime.now(UTC) - timedelta(days=period)
        checks = await self._health_check_repo.get_since(url_id, since=since)
        return self._stats_service.compute(checks)

    async def get_status(self, url_id: int) -> DegradationStatus:
        checks = await self._health_check_repo.get_by_url_id(
            url_id, limit=settings.degradation_window_size
        )
        return self._degradation_detector.detect(checks)

    async def get_status_map(
        self, url_ids: Sequence[int]
    ) -> dict[int, DegradationStatus]:
        grouped = await self._health_check_repo.get_recent_by_url_ids(
            url_ids, limit=settings.degradation_window_size
        )
        return {
            url_id: self._degradation_detector.detect(checks)
            for url_id, checks in grouped.items()
        }
