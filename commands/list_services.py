from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from commands.handlers import list_services_command_handler


async def list_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services_str = list_services_command_handler(update.effective_chat.id)
    await update.message.reply_text(''.join(services_str), parse_mode=ParseMode.MARKDOWN)
