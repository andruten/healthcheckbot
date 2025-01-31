import logging
from telegram import Update
from telegram.ext import ContextTypes

from command_handlers import add_service_command_handler


logger = logging.getLogger(__name__)


async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Validate arguments
    if len(context.args) != 2:
        await update.message.reply_text('Please, use /add <name> <url>')
        return

    name, url = context.args

    service = add_service_command_handler(update.effective_chat.id, name, url)

    await update.message.reply_text(f'ok! I\'ve added {service}')
