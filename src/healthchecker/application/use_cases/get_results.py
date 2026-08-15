from healthchecker.domain.repositories.health_check_repository import (
    HealthCheckRepository,
)
from healthchecker.domain.services.degradation_service import (
    DegradationDetector,
    DegradationStatus,
)
from healthchecker.infrastructure.config import settings


class GetResultsUseCase:
    def __init__(
        self,
        health_check_repo: HealthCheckRepository,
        degradation_detector: DegradationDetector | None = None,
    ):
        self._health_check_repo = health_check_repo
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

    async def get_history(self, url_id: int, limit: int = 5):
        return await self._health_check_repo.get_by_url_id(url_id, limit=limit)

    async def get_status(self, url_id: int) -> DegradationStatus:
        checks = await self._health_check_repo.get_by_url_id(
            url_id, limit=settings.degradation_window_size
        )
        return self._degradation_detector.detect(checks)
