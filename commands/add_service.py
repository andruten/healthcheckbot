import logging
from telegram import Update
from telegram.ext import ContextTypes

from command_handlers import add_service_command_handler
from models import HEALTHCHECK_BACKENDS


logger = logging.getLogger(__name__)


async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Validate arguments
    if len(context.args) != 4:
        await update.message.reply_text('Please, use /add <service_type> <name> <domain> <port>')
        return

    service_type, name, domain, port = context.args
    if service_type.lower() not in HEALTHCHECK_BACKENDS.keys():
        await update.message.reply_text(f'<service_type> must be {", ".join(HEALTHCHECK_BACKENDS.keys())}')
        return
    try:
        port = int(port)
    except ValueError:
        await update.message.reply_text('<port> must be a number')
        return

    service = add_service_command_handler(update.effective_chat.id, service_type, name, domain, port)

    await update.message.reply_text(f'ok! I\'ve added {service}')
