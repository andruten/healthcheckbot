from telegram import Update
from telegram.ext import ContextTypes

from healthchecker.application.use_cases.manage_urls import ManageUrlsUseCase


class DeleteUrlHandler:
    def __init__(self, manage_urls: ManageUrlsUseCase):
        self._manage_urls = manage_urls

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("Usage: /delete <id>\nExample: /delete 3")
            return

        url_id = int(context.args[0])
        url = await self._manage_urls.get_by_id(url_id)
        if not url:
            await update.message.reply_text(f"URL with ID {url_id} not found.")
            return

        await self._manage_urls.delete(url_id)
        await update.message.reply_text(
            f"🗑️ Deleted *{url.name}* (ID: {url_id})", parse_mode="Markdown"
        )
