import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import date

from healthchecker.application.use_cases.check_all_urls import CheckAllUrlsUseCase
from healthchecker.application.use_cases.consolidate_summaries import (
    ConsolidateDailySummariesUseCase,
)
from healthchecker.domain.repositories.alert_repository import AlertRepository
from healthchecker.infrastructure.config import settings

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(
        self,
        check_all_urls: CheckAllUrlsUseCase,
        consolidate_use_case: ConsolidateDailySummariesUseCase | None = None,
        alert_repo: AlertRepository | None = None,
        send_alert: Callable[[str], Awaitable[None]] | None = None,
    ):
        self._check_all_urls = check_all_urls
        self._consolidate = consolidate_use_case
        self._alert_repo = alert_repo
        self._send_alert = send_alert
        self._running = False
        self._last_consolidation_date: date | None = None

    async def start(self):
        self._running = True
        logger.info("Scheduler started (interval: %ds)", settings.check_interval_sec)

        await self._try_consolidation()

        while self._running:
            try:
                alerts = await self._check_all_urls.execute()
                if alerts:
                    logger.info("%d alerts generated", len(alerts))
                    await self._dispatch_alerts(alerts)
            except Exception as e:
                logger.error("Scheduler error: %s", e, exc_info=True)

            if self._should_consolidate():
                await self._try_consolidation()

            await asyncio.sleep(settings.check_interval_sec)

    async def stop(self):
        self._running = False
        logger.info("Scheduler stopped")

    def _should_consolidate(self) -> bool:
        today = date.today()
        return self._last_consolidation_date != today

    async def _dispatch_alerts(self, alerts):
        for alert in alerts:
            sent = True
            if self._send_alert:
                try:
                    await self._send_alert(alert.message)
                except Exception as e:
                    sent = False
                    logger.error("Failed to send alert: %s", e, exc_info=True)
            if sent and self._alert_repo and alert.id is not None:
                await self._alert_repo.mark_as_sent(alert.id)

    async def _try_consolidation(self):
        if not self._consolidate:
            return
        try:
            count = await self._consolidate.execute()
            self._last_consolidation_date = date.today()
            if count:
                logger.info("Consolidation complete: %d summaries created", count)
        except Exception as e:
            logger.error("Consolidation error: %s", e, exc_info=True)
