from telegram import Update
from telegram.ext import ContextTypes

from command_handlers import remove_services_command_handler


async def remove_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await update.message.reply_text('Please, use /remove <name>')
        return
    name, = context.args

    remove_services_command_handler(name, str(update.effective_chat.id))

    await update.message.reply_text(f'ok! I\'ve removed {name}')
