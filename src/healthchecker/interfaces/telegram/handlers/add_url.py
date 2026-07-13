import re

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from healthchecker.application.use_cases.manage_urls import ManageUrlsUseCase
from healthchecker.interfaces.telegram.markdown import markdown_escape


class AddUrlHandler:
    def __init__(self, manage_urls: ManageUrlsUseCase):
        self._manage_urls = manage_urls

    def handler(self):
        return CommandHandler("add", self.handle)

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "Usage: /add <url> [name] [--alert-days N]\n"
                "Example: /add https://example.com MySite --alert-days 14"
            )
            return

        args = list(context.args)
        alert_days = 30
        name = None
        url = None

        if "--alert-days" in args:
            idx = args.index("--alert-days")
            if idx + 1 < len(args):
                alert_days = int(args[idx + 1])
                args = args[:idx] + args[idx + 2 :]
            else:
                args.remove("--alert-days")

        if args:
            url = args[0]
            if len(args) > 1:
                name = " ".join(args[1:])

        if not url or not self._is_valid_url(url):
            await update.message.reply_text(
                "Invalid URL. Please provide a valid HTTP or HTTPS URL."
            )
            return

        try:
            created = await self._manage_urls.add(
                url=url, name=name, alert_before_days=alert_days
            )
            await update.message.reply_text(
                f"✅ Added URL *{markdown_escape(created.name)}* (ID: {created.id})\n"
                f"URL: `{markdown_escape(created.url)}`\n"
                f"SSL alert threshold: {alert_days} days",
                parse_mode="Markdown",
            )
        except Exception as e:
            await update.message.reply_text(f"Error adding URL: {e}")

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        return bool(re.match(pattern, url))
