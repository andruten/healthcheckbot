from telegram import Update
from telegram.ext import ContextTypes

from healthchecker.application.use_cases.manage_urls import ManageUrlsUseCase
from healthchecker.application.use_cases.get_results import GetResultsUseCase
from healthchecker.interfaces.telegram.markdown import markdown_escape


class ListUrlsHandler:
    def __init__(self, manage_urls: ManageUrlsUseCase, get_results: GetResultsUseCase):
        self._manage_urls = manage_urls
        self._get_results = get_results

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        urls = await self._manage_urls.list_all()

        if not urls:
            await update.message.reply_text(
                "No URLs are being monitored. Use /add to add one."
            )
            return

        lines = [f"📋 *Monitored URLs ({len(urls)}):*\n"]
        for url in urls:
            latest = await self._get_results.get_latest(url.id)
            status_line = (
                self._format_status(latest, url.alert_before_days)
                if latest
                else "⏳ Not checked yet"
            )
            lines.append(
                f"{url.id}. *{markdown_escape(url.name)}*\n"
                f"   `{markdown_escape(url.url)}`\n"
                f"   {status_line}\n"
            )

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    @staticmethod
    def _format_status(check, alert_before_days: int = 30):
        if check.error_message:
            return f"❌ Error: {markdown_escape(check.error_message)}"

        http_part = f"HTTP {check.http_status}"
        ttfb_part = f"{check.ttfb_ms:.0f}ms" if check.ttfb_ms else ""
        ssl_part = (
            f"SSL: {check.ssl_days_remaining}d"
            if check.ssl_days_remaining is not None
            else ""
        )

        ssl_expiry = ""
        if check.ssl_expiration_date:
            ssl_expiry = f"Expires: {check.ssl_expiration_date.strftime('%Y-%m-%d')}"

        parts = [p for p in [http_part, ttfb_part, ssl_part, ssl_expiry] if p]

        if not check.is_healthy:
            status_icon = "❌"
        elif (
            check.ssl_days_remaining is not None
            and check.ssl_days_remaining <= alert_before_days
        ):
            status_icon = "⚠️"
        else:
            status_icon = "✅"

        return f"{status_icon} {' | '.join(parts)}"
