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
                "Examples:\n"
                "/add https://example.com MySite --alert-days 14\n"
                "/add imaps://mail.example.com MyMail\n"
                "/add mail.example.com:993 MyMail"
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
                "Invalid URL. Please provide a valid HTTP/HTTPS URL, a TLS URL "
                "(imaps://, pop3s://, smtps://, ftps://, ldaps://) or host:port."
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
        except Exception:  # noqa: BLE001
            await update.message.reply_text(
                "Error adding URL. Please check the URL and try again."
            )

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        tls_schemes = r"https?|imaps|pop3s|smtps|ftps|ldaps"
        with_scheme = rf"^({tls_schemes})://[^\s/$.?#].[^\s]*$"
        host_port = r"^([^\s/:?#]+\.[^\s/:?#]+):(\d{1,5})$"
        if re.match(with_scheme, url):
            return True
        match = re.match(host_port, url)
        return bool(match and 1 <= int(match.group(2)) <= 65535)
