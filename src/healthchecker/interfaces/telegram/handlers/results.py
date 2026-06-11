from telegram import Update
from telegram.ext import ContextTypes

from healthchecker.application.use_cases.get_results import GetResultsUseCase
from healthchecker.application.use_cases.manage_urls import ManageUrlsUseCase
from healthchecker.domain.repositories.daily_summary_repository import (
    DailySummaryRepository,
)


class ResultsHandler:
    def __init__(
        self,
        get_results: GetResultsUseCase,
        manage_urls: ManageUrlsUseCase,
        summary_repo: DailySummaryRepository | None = None,
    ):
        self._get_results = get_results
        self._manage_urls = manage_urls
        self._summary_repo = summary_repo

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(
                "Usage: /results <id> [--limit N]\nExample: /results 1 --limit 10"
            )
            return

        url_id = int(context.args[0])
        limit = 5

        if "--limit" in context.args:
            idx = context.args.index("--limit")
            if idx + 1 < len(context.args):
                limit = int(context.args[idx + 1])

        url = await self._manage_urls.get_by_id(url_id)
        if not url:
            await update.message.reply_text(f"URL with ID {url_id} not found.")
            return

        checks = await self._get_results.get_history(url_id, limit=limit)
        lines = []

        if checks:
            lines.append(f"📊 *Results for {url.name}* (last {len(checks)} checks)\n")
            for c in checks:
                lines.append(self._format_raw_check(c))
        else:
            lines.append(f"📊 *Results for {url.name}*\n")

        remaining = limit - len(checks)
        if remaining > 0 and self._summary_repo:
            summaries = await self._summary_repo.get_by_url_id(url_id, limit=remaining)
            if summaries:
                if not lines or len(lines) == 1:
                    lines.append("📋 *Daily summaries:*\n")
                for s in summaries:
                    lines.append(self._format_summary(s))

        if len(lines) <= 1:
            await update.message.reply_text(
                f"No health checks yet for *{url.name}*.", parse_mode="Markdown"
            )
            return

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    @staticmethod
    def _format_raw_check(c) -> str:
        icon = "✅" if c.is_healthy else "❌"
        parts = [icon, f"HTTP {c.http_status}" if c.http_status else "N/A"]
        if c.ttfb_ms is not None:
            parts.append(f"{c.ttfb_ms:.0f}ms")
        if c.ssl_days_remaining is not None:
            parts.append(f"SSL: {c.ssl_days_remaining}d")
        if c.ssl_expiration_date:
            parts.append(f"Expires: {c.ssl_expiration_date.strftime('%Y-%m-%d')}")
        if c.error_message:
            parts.append(f"Error: {c.error_message}")
        timestamp = c.checked_at.strftime("%Y-%m-%d %H:%M:%S") if c.checked_at else "?"
        return f"`{timestamp}` — {' | '.join(parts)}"

    @staticmethod
    def _format_summary(s) -> str:
        icon = "✅" if s.healthy_count > s.unhealthy_count else "❌"
        parts = [icon, f"HTTP {s.last_http_status}" if s.last_http_status else "N/A"]
        if s.avg_ttfb_ms is not None:
            parts.append(f"avg {s.avg_ttfb_ms:.0f}ms")
        if s.min_ssl_days_remaining is not None:
            parts.append(f"SSL min: {s.min_ssl_days_remaining}d")
        if s.last_ssl_expiration_date:
            parts.append(f"Expires: {s.last_ssl_expiration_date.strftime('%Y-%m-%d')}")
        parts.append(f"{s.healthy_count}/{s.checks_count} ok")
        return f"`{s.summary_date}` — {' | '.join(parts)}"
