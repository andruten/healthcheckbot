from telegram import Update
from telegram.ext import ContextTypes

from healthchecker.application.use_cases.check_all_urls import CheckAllUrlsUseCase


class CheckNowHandler:
    def __init__(self, check_all_urls: CheckAllUrlsUseCase):
        self._check_all_urls = check_all_urls

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔍 Running health checks...")
        alerts = await self._check_all_urls.execute()
        await update.message.reply_text(
            f"✅ Health checks completed.\nAlerts generated: {len(alerts)}"
            if alerts
            else "✅ Health checks completed. No alerts."
        )
