import logging
import os

import environ
from telegram import Update
from telegram.ext import Application, CallbackContext, CommandHandler

from command_handlers import (add_service_command_handler, chat_services_checker_command_handler,
                              list_services_command_handler, remove_services_command_handler)
from models import HEALTHCHECK_BACKENDS

abspath = os.path.abspath(__file__)
directory_name = os.path.dirname(abspath)
os.chdir(directory_name)

env = environ.Env()
environ.Env.read_env()

BOT_TOKEN = env.str('BOT_TOKEN')
POLLING_INTERVAL = env.int('POLLING_INTERVAL', 60)
ALLOW_LIST_CHAT_IDS = env.list('ALLOW_LIST_CHAT_IDS')
LOG_LEVEL = logging.DEBUG if env.str('LOG_LEVEL') == 'DEBUG' else logging.INFO

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=LOG_LEVEL)

logger = logging.getLogger(__name__)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.error('Update "%s" caused error "%s"', update, context.error)


def check_all_services(context: CallbackContext):
    chat_fetched_services = chat_services_checker_command_handler()

    for chat_id in chat_fetched_services:
        fetched_services = chat_fetched_services[chat_id]
        for unhealthy_service in fetched_services['unhealthy']:
            text = f'{unhealthy_service} is down 🤕!'
            context.bot.send_message(chat_id=chat_id, text=text)
        for healthy_service in fetched_services['healthy']:
            text = f'{healthy_service} is fixed now 😅!'
            context.bot.send_message(chat_id=chat_id, text=text)


async def add_service(update: Update, context: CallbackContext) -> None:
    if str(update.effective_chat.id) not in ALLOW_LIST_CHAT_IDS:
        await update.message.reply_text('You\'re not allowed to use this command')
        return

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


async def remove_service(update: Update, context: CallbackContext) -> None:
    if str(update.effective_chat.id) not in ALLOW_LIST_CHAT_IDS:
        await update.message.reply_text('You\'re not allowed to use this command')
        return

    if len(context.args) != 1:
        await update.message.reply_text('Please, use /remove <name>')
        return
    name, = context.args

    remove_services_command_handler(name, str(update.effective_chat.id))

    await update.message.reply_text(f'ok! I\'ve removed {name}')


async def list_services(update: Update, context: CallbackContext) -> None:
    if str(update.effective_chat.id) not in ALLOW_LIST_CHAT_IDS:
        await update.message.reply_text('You\'re not allowed to use this command')
        return

    services_str = list_services_command_handler(str(update.effective_chat.id))

    await update.message.reply_text(f'I\'m polling{"".join(services_str)}')


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    job_queue = application.job_queue
    job_queue.run_repeating(check_all_services, POLLING_INTERVAL)

    application.add_handler(CommandHandler('add', add_service))
    application.add_handler(CommandHandler('remove', remove_service))
    application.add_handler(CommandHandler('list', list_services))

    application.add_error_handler(error)

    application.run_polling()


if __name__ == '__main__':
    main()
