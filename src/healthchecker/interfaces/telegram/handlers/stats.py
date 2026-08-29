from telegram import Update
from telegram.ext import ContextTypes

from healthchecker.application.use_cases.get_stats import GetStatsUseCase
from healthchecker.application.use_cases.manage_urls import ManageUrlsUseCase
from healthchecker.domain.models.health_check_stats import HealthCheckStats
from healthchecker.infrastructure.config import settings
from healthchecker.interfaces.telegram.markdown import markdown_escape


class StatsHandler:
    def __init__(self, get_stats: GetStatsUseCase, manage_urls: ManageUrlsUseCase):
        self._get_stats = get_stats
        self._manage_urls = manage_urls

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(
                "Usage: /stats <id> [--days N]\nExample: /stats 1 --days 7"
            )
            return

        url_id = int(context.args[0])
        days = settings.stats_default_days

        if "--days" in context.args:
            idx = context.args.index("--days")
            if idx + 1 < len(context.args) and context.args[idx + 1].isdigit():
                days = int(context.args[idx + 1])
            else:
                await update.message.reply_text(
                    "Usage: /stats <id> [--days N]\nExample: /stats 1 --days 7"
                )
                return

        if days < 1:
            days = 1
        elif days > settings.stats_max_days:
            days = settings.stats_max_days
            await update.message.reply_text(
                f"⚠️ Max allowed period is {settings.stats_max_days} days "
                f"(raw check retention). Showing last {days}d."
            )

        url = await self._manage_urls.get_by_id(url_id)
        if not url:
            await update.message.reply_text(f"URL with ID {url_id} not found.")
            return

        stats = await self._get_stats.get_stats(url_id, days=days)

        if stats.total_checks == 0:
            await update.message.reply_text(
                f"No health checks in the last {days}d for "
                f"*{markdown_escape(url.name)}*.",
                parse_mode="Markdown",
            )
            return

        lines = [f"📊 *Stats for {markdown_escape(url.name)}* (last {days}d)\n"]
        lines.append(self._format_uptime(stats))
        lines.append(self._format_ttfb(stats))
        lines.append(self._format_ssl(stats))
        lines.append(self._format_streak(stats))

        degradation = await self._get_stats.get_status(url_id)
        if degradation.is_degraded:
            lines.append(self._format_degradation(degradation))

        latest = await self._get_stats.get_latest(url_id)
        if latest:
            lines.append("")
            lines.append(self._format_latest(latest))

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    @staticmethod
    def _format_uptime(s: HealthCheckStats) -> str:
        icon = "✅" if s.uptime_pct is not None and s.uptime_pct >= 99.0 else "⚠️"
        failures = s.total_checks - s.healthy_count
        parts = [icon, f"Uptime: {s.uptime_pct:.1f}%", f"({failures} failures)"]
        if s.last_failure_at:
            parts.append(f"last at {s.last_failure_at.strftime('%m-%d %H:%M')}")
        return " ".join(parts)

    @staticmethod
    def _format_ttfb(s: HealthCheckStats) -> str:
        if s.ttfb_samples == 0:
            return "⚡ TTFB: no data"
        return (
            f"⚡ TTFB: avg {s.ttfb_avg_ms:.0f}ms | p95 {s.ttfb_p95_ms:.0f}ms | "
            f"min {s.ttfb_min_ms:.0f}ms | max {s.ttfb_max_ms:.0f}ms"
        )

    @staticmethod
    def _format_ssl(s: HealthCheckStats) -> str:
        if s.min_ssl_days_remaining is None:
            return "🔗 SSL: no data"
        icon = "✅" if s.min_ssl_days_remaining > settings.default_alert_days else "⚠️"
        parts = [icon, f"SSL: {s.min_ssl_days_remaining}d"]
        if s.last_ssl_expiration_date:
            parts.append(f"(expires {s.last_ssl_expiration_date.strftime('%Y-%m-%d')})")
        return " ".join(parts)

    @staticmethod
    def _format_streak(s: HealthCheckStats) -> str:
        if s.current_streak >= 0:
            return f"🔥 Streak: {s.current_streak} ok"
        return f"🔥 Streak: {abs(s.current_streak)} failing"

    @staticmethod
    def _format_degradation(status) -> str:
        if status.reason and status.reason.value == "ttfb_increase":
            detail = (
                f"TTFB up from {status.baseline_ttfb_ms:.0f}ms to "
                f"{status.current_ttfb_ms:.0f}ms"
            )
        else:
            detail = f"{status.failure_count}/{status.total_checks} checks failing"
        return f"⚠️ *Degraded:* {markdown_escape(detail)}"

    @staticmethod
    def _format_latest(c) -> str:
        icon = "✅" if c.is_healthy else "❌"
        parts = [icon, f"HTTP {c.http_status}" if c.http_status else "N/A"]
        if c.ttfb_ms is not None:
            parts.append(f"{c.ttfb_ms:.0f}ms")
        if c.error_message:
            parts.append(f"Error: {markdown_escape(c.error_message)}")
        timestamp = c.checked_at.strftime("%Y-%m-%d %H:%M:%S") if c.checked_at else "?"
        return f"Last check: `{timestamp}` — {' | '.join(parts)}"
