import asyncio
import logging
from datetime import datetime, timezone

from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.models.alert import Alert
from healthchecker.domain.models.url import Url
from healthchecker.domain.repositories.url_repository import UrlRepository
from healthchecker.domain.repositories.health_check_repository import (
    HealthCheckRepository,
)
from healthchecker.domain.repositories.alert_repository import AlertRepository
from healthchecker.domain.services.health_check_service import HealthCheckService
from healthchecker.infrastructure.checker.http_checker import HttpHealthChecker
from healthchecker.infrastructure.checker.ssl_checker import SslChecker

logger = logging.getLogger(__name__)


class CheckAllUrlsUseCase:
    def __init__(
        self,
        url_repo: UrlRepository,
        health_check_repo: HealthCheckRepository,
        alert_repo: AlertRepository,
        http_checker: HttpHealthChecker,
        ssl_checker: SslChecker,
    ):
        self._url_repo = url_repo
        self._health_check_repo = health_check_repo
        self._alert_repo = alert_repo
        self._http_checker = http_checker
        self._ssl_checker = ssl_checker

    async def execute(self) -> list[Alert]:
        urls = await self._url_repo.get_all_active()
        logger.debug("Running health checks for %d URLs", len(urls))
        results = await asyncio.gather(
            *[self._check_one(url) for url in urls]
        )
        return [alert for batch in results for alert in batch]

    async def _check_one(self, url: Url) -> list[Alert]:
        try:
            previous_check = await self._health_check_repo.get_latest_by_url_id(
                url.id
            )

            http_status, ttfb_ms, error = await self._http_checker.check(url.url)

            ssl_info = None
            if url.url.startswith("https"):
                ssl_info = await self._ssl_checker.check(url.url)

            ssl_expiry = ssl_info.expiration_date if ssl_info else None
            ssl_days = ssl_info.days_remaining if ssl_info else None
            is_healthy = error is None and (
                http_status is not None and 200 <= http_status < 400
            )

            check = HealthCheck(
                id=None,
                url_id=url.id,
                http_status=http_status,
                ttfb_ms=ttfb_ms,
                ssl_expiration_date=ssl_expiry,
                ssl_days_remaining=ssl_days,
                is_healthy=is_healthy,
                error_message=error,
                checked_at=datetime.now(timezone.utc),
            )

            await self._health_check_repo.save(check)

            alerts: list[Alert] = []

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
                        http_status,
                        error,
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
                        http_status,
                        ttfb_ms,
                    )
                    await self._alert_repo.save(alert)
                    alerts.append(alert)

            return alerts

        except Exception as e:
            logger.error("Error checking URL %s: %s", url.url, e, exc_info=True)
            return []
