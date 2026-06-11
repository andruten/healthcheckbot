import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CommandHandler,
    MessageHandler,
    filters,
)

from healthchecker.infrastructure.config import settings
from healthchecker.interfaces.telegram.handlers.add_url import AddUrlHandler
from healthchecker.interfaces.telegram.handlers.list_urls import ListUrlsHandler
from healthchecker.interfaces.telegram.handlers.delete_url import DeleteUrlHandler
from healthchecker.interfaces.telegram.handlers.check_now import CheckNowHandler
from healthchecker.interfaces.telegram.handlers.results import ResultsHandler
from healthchecker.application.use_cases.manage_urls import ManageUrlsUseCase
from healthchecker.application.use_cases.get_results import GetResultsUseCase
from healthchecker.application.use_cases.check_all_urls import CheckAllUrlsUseCase
from healthchecker.domain.repositories.daily_summary_repository import (
    DailySummaryRepository,
)

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(
        self,
        manage_urls: ManageUrlsUseCase,
        get_results: GetResultsUseCase,
        check_all_urls: CheckAllUrlsUseCase,
        summary_repo: DailySummaryRepository | None = None,
    ):
        self._manage_urls = manage_urls
        self._get_results = get_results
        self._check_all_urls = check_all_urls
        self._summary_repo = summary_repo
        self._app: Application | None = None

    async def start(self):
        self._app = Application.builder().token(settings.telegram_bot_token).build()

        if settings.allowed_chat_ids:
            self._app.add_handler(
                MessageHandler(
                    ~filters.Chat(chat_id=settings.allowed_chat_ids) & filters.COMMAND,
                    self._unauthorized,
                ),
                group=-1,
            )

        self._app.add_handler(CommandHandler("help", self._cmd_help))

        add_handler = AddUrlHandler(self._manage_urls)
        self._app.add_handler(add_handler.handler())

        self._app.add_handler(
            CommandHandler(
                "list", ListUrlsHandler(self._manage_urls, self._get_results).handle
            )
        )
        self._app.add_handler(
            CommandHandler("delete", DeleteUrlHandler(self._manage_urls).handle)
        )
        self._app.add_handler(
            CommandHandler("check", CheckNowHandler(self._check_all_urls).handle)
        )
        self._app.add_handler(
            CommandHandler(
                "results",
                ResultsHandler(
                    self._get_results, self._manage_urls, self._summary_repo
                ).handle,
            )
        )

        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()
        logger.info("Telegram bot started")

    async def stop(self):
        if self._app:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
            logger.info("Telegram bot stopped")

    async def send_alert(self, message: str):
        if not self._app:
            return
        bot = self._app.bot
        chat_ids = (
            settings.allowed_chat_ids
            if settings.allowed_chat_ids
            else await self._get_authorized_chat_ids()
        )
        for chat_id in chat_ids:
            try:
                await bot.send_message(
                    chat_id=chat_id, text=message, parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(
                    "Failed to send alert to chat %s: %s", chat_id, e, exc_info=True
                )

    async def _get_authorized_chat_ids(self) -> set[int]:
        chat_ids: set[int] = set()
        updates = await self._app.updater.bot.get_updates()
        for update in updates:
            if update.effective_chat:
                chat_ids.add(update.effective_chat.id)
        return chat_ids

    async def _unauthorized(self, update: Update, context):
        await update.message.reply_text("You are not authorized to use this bot.")
        raise ApplicationHandlerStop

    async def _cmd_help(self, update: Update, context):
        text = (
            "🤖 *Health Checker Bot*\n\n"
            "Monitor your URLs with HTTP status, TTFB, and SSL certificate tracking.\n\n"
            "*Commands:*\n"
            "/add `<url>` `[name]` `[--alert-days N]` — Add a URL to monitor\n"
            "/list — Show all monitored URLs\n"
            "/delete `<id>` — Remove a URL\n"
            "/check `[id]` — Run health check now\n"
            "/results `<id>` `[--limit N]` — Show check history\n"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
