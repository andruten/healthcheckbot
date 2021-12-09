import logging
import os
import environ
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler

from models import ServiceManager, Service
from persistence import PersistenceBackend

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
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def check_all_services(context: CallbackContext):
    chat_ids = PersistenceBackend.get_all_chat_ids()
    for chat_id in chat_ids:
        persistence = PersistenceBackend.create(chat_id)
        services = ServiceManager(persistence).fetch_active()
        failing_services = []
        for service in services:
            service_response = service.healthcheck_backend.check()
            if not service_response:
                failing_services.append(service)
        if failing_services:
            for failing_service in failing_services:
                text = f'{failing_service} is down!'
                context.bot.send_message(chat_id=chat_id, text=text)


def add_service(update: Update, context: CallbackContext) -> None:
    if str(update.effective_chat.id) not in ALLOW_LIST_CHAT_IDS:
        update.message.reply_text(f'You\'re not allowed to use this command')
    # Validate arguments
    if len(context.args) != 4:
        update.message.reply_text('Please, use /add <service_type> <name> <domain> <port>')
        return
    service_type, name, domain, port = context.args
    if service_type.lower() not in Service.HEALTHCHECK_BACKENDS.keys():
        update.message.reply_text(f'<service_type> must be {", ".join(Service.HEALTHCHECK_BACKENDS.keys())}')
        return
    try:
        port = int(port)
    except ValueError:
        update.message.reply_text(f'<port> must be a number')
        return
    # All validations are passing so Service will be added
    persistence = PersistenceBackend.create(update.effective_chat.id)
    service = ServiceManager(persistence).add(service_type, name, domain, port)
    update.message.reply_text(f'ok! I\'ve added {service}')


def remove_service(update: Update, context: CallbackContext) -> None:
    if str(update.effective_chat.id) not in ALLOW_LIST_CHAT_IDS:
        update.message.reply_text(f'You\'re not allowed to use this command')
    if len(context.args) != 1:
        update.message.reply_text('Please, use /remove <name>')
        return
    name, = context.args
    persistence = PersistenceBackend.create(update.effective_chat.id)
    ServiceManager(persistence).remove(name)
    update.message.reply_text(f'ok! I\'ve removed {name}')


def list_services(update: Update, context: CallbackContext) -> None:
    if str(update.effective_chat.id) not in ALLOW_LIST_CHAT_IDS:
        update.message.reply_text(f'You\'re not allowed to use this command')
    persistence = PersistenceBackend.create(update.effective_chat.id)
    all_services = ServiceManager(persistence).fetch_all()
    services_str = [f'\n{service}' for service in all_services]
    update.message.reply_text(f'I\'m polling{"".join(services_str)}')


def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    job = updater.job_queue
    job.run_repeating(check_all_services, POLLING_INTERVAL)
    dispatcher.add_handler(CommandHandler('add', add_service))
    dispatcher.add_handler(CommandHandler('remove', remove_service))
    dispatcher.add_handler(CommandHandler('list', list_services))
    dispatcher.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
