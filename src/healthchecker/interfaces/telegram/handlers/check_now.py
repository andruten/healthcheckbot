import logging
from collections.abc import Awaitable, Callable

from telegram import Update
from telegram.ext import ContextTypes

from healthchecker.application.use_cases.check_all_urls import CheckAllUrlsUseCase
from healthchecker.domain.models.alert import Alert
from healthchecker.domain.repositories.alert_repository import AlertRepository

logger = logging.getLogger(__name__)


class CheckNowHandler:
    def __init__(
        self,
        check_all_urls: CheckAllUrlsUseCase,
        alert_repo: AlertRepository | None = None,
        send_alert: Callable[[str], Awaitable[None]] | None = None,
    ):
        self._check_all_urls = check_all_urls
        self._alert_repo = alert_repo
        self._send_alert = send_alert

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔍 Running health checks...")
        alerts = await self._check_all_urls.execute()
        await self._dispatch_alerts(alerts)
        await update.message.reply_text(
            f"✅ Health checks completed.\nAlerts generated: {len(alerts)}"
            if alerts
            else "✅ Health checks completed. No alerts."
        )

    async def _dispatch_alerts(self, alerts: list[Alert]):
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
