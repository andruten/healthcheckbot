import asyncio
import logging
from datetime import UTC, datetime

from healthchecker.domain.models.alert import Alert
from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.models.url import Url
from healthchecker.domain.repositories.alert_repository import AlertRepository
from healthchecker.domain.repositories.health_check_repository import (
    HealthCheckRepository,
)
from healthchecker.domain.repositories.url_repository import UrlRepository
from healthchecker.domain.services.degradation_service import DegradationDetector
from healthchecker.domain.services.health_check_service import HealthCheckService
from healthchecker.infrastructure.checker.http_checker import HttpHealthChecker
from healthchecker.infrastructure.checker.ssl_checker import SslChecker
from healthchecker.infrastructure.config import settings

logger = logging.getLogger(__name__)


class CheckAllUrlsUseCase:
    def __init__(
        self,
        url_repo: UrlRepository,
        health_check_repo: HealthCheckRepository,
        alert_repo: AlertRepository,
        http_checker: HttpHealthChecker,
        ssl_checker: SslChecker,
        degradation_detector: DegradationDetector | None = None,
        degradation_enabled: bool | None = None,
    ):
        self._url_repo = url_repo
        self._health_check_repo = health_check_repo
        self._alert_repo = alert_repo
        self._http_checker = http_checker
        self._ssl_checker = ssl_checker
        self._degradation_enabled = (
            settings.degradation_enabled
            if degradation_enabled is None
            else degradation_enabled
        )
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

    async def execute(self) -> list[Alert]:
        urls = await self._url_repo.get_all_active()
        logger.debug("Running health checks for %d URLs", len(urls))
        results = await asyncio.gather(*[self._check_one(url) for url in urls])
        return [alert for batch in results for alert in batch]

    async def _check_one(self, url: Url) -> list[Alert]:
        try:
            window_size = settings.degradation_window_size
            history = await self._health_check_repo.get_by_url_id(
                url.id, limit=window_size
            )
            previous_check = history[0] if history else None

            http_result = await self._http_checker.check(url.url)

            ssl_info = None
            if url.url.startswith("https"):
                ssl_info = await self._ssl_checker.check(url.url)

            ssl_expiry = ssl_info.expiration_date if ssl_info else None
            ssl_days = ssl_info.days_remaining if ssl_info else None
            is_healthy = http_result.error is None and (
                http_result.status_code is not None
                and 200 <= http_result.status_code < 400
            )

            check = HealthCheck(
                id=None,
                url_id=url.id,
                http_status=http_result.status_code,
                ttfb_ms=http_result.ttfb_ms,
                ssl_expiration_date=ssl_expiry,
                ssl_days_remaining=ssl_days,
                is_healthy=is_healthy,
                error_message=http_result.error,
                checked_at=datetime.now(UTC),
            )

            await self._health_check_repo.save(check)

            alerts: list[Alert] = []

            if self._degradation_enabled:
                previous_status = self._degradation_detector.detect(history)
                current_status = self._degradation_detector.detect(
                    [check, *history[: window_size - 1]]
                )
                if current_status.is_degraded and not previous_status.is_degraded:
                    alert = HealthCheckService.build_degradation_start_alert(
                        url.id, url.name, current_status
                    )
                    await self._alert_repo.save(alert)
                    alerts.append(alert)
                elif not current_status.is_degraded and previous_status.is_degraded:
                    alert = HealthCheckService.build_degradation_recover_alert(
                        url.id, url.name, current_status
                    )
                    await self._alert_repo.save(alert)
                    alerts.append(alert)

            if ssl_days is not None and HealthCheckService.should_alert_ssl(
                ssl_days, url.alert_before_days
            ):
                previous_ssl_ok = (
                    previous_check is None
                    or previous_check.ssl_days_remaining is None
                    or previous_check.ssl_days_remaining > url.alert_before_days
                )
                if previous_ssl_ok:
                    alert = HealthCheckService.build_ssl_alert(
                        url.id,
                        url.name,
                        ssl_days,
                        url.alert_before_days,
                        ssl_expiry,
                    )
                    await self._alert_repo.save(alert)
                    alerts.append(alert)

            if not is_healthy:
                was_healthy = previous_check is None or previous_check.is_healthy
                if was_healthy:
                    alert = HealthCheckService.build_http_down_alert(
                        url.id,
                        url.name,
                        http_result.status_code,
                        http_result.error,
                    )
                    await self._alert_repo.save(alert)
                    alerts.append(alert)
            else:
                was_unhealthy = (
                    previous_check is not None and not previous_check.is_healthy
                )
                if was_unhealthy:
                    alert = HealthCheckService.build_http_up_alert(
                        url.id,
                        url.name,
                        http_result.status_code,
                        http_result.ttfb_ms,
                    )
                    await self._alert_repo.save(alert)
                    alerts.append(alert)

            return alerts

        except Exception:
            logger.exception("Error checking URL %s", url.url)
            return []
