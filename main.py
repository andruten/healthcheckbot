import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler

from models import ServiceManager, Service

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

load_dotenv()

# Enable logging
LOG_LEVEL = logging.DEBUG if os.environ.get('LOG_LEVEL') == 'DEBUG' else logging.INFO

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=LOG_LEVEL
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
try:
    POLLING_INTERVAL = int(os.environ.get('POLLING_INTERVAL'))
except ValueError:
    POLLING_INTERVAL = 60


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def check_all_services(context: CallbackContext):
    services = ServiceManager().fetch_active()
    failing_services = []
    for service in services:
        service_response = service.backend.check()
        if not service_response:
            failing_services.append(service)
    if failing_services:
        for failing_service in failing_services:
            text = f'{failing_service} is down!'
            context.bot.send_message(chat_id=CHAT_ID, text=text)


def add(update: Update, context: CallbackContext) -> None:
    # Validate arguments
    if len(context.args) != 4:
        update.message.reply_text('Please, use /add <service_type> <name> <domain> <port>')
        return
    service_type, name, domain, port = context.args
    if service_type.lower() not in Service.BACKENDS.keys():
        update.message.reply_text(f'service_type must be {", ".join(Service.BACKENDS.keys())}')
        return
    try:
        port = int(port)
    except ValueError:
        update.message.reply_text(f'port must be a number')
    # Add service
    service = ServiceManager().add(service_type, name, domain, port)
    update.message.reply_text(f'Ok! I\'ve added {service}')


def remove(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text('Please, use /remove <name>')
        return
    name, = context.args
    ServiceManager().remove(name)
    update.message.reply_text(f'Ok! I\'ve removed {name}')


def list_services(update: Update, context: CallbackContext) -> None:
    all_services = ServiceManager().fetch_all()
    services_str = [f'\n- {service.__repr__()}' for service in all_services]
    update.message.reply_text(f'I\'m polling: {"".join(services_str)}')


def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    job = updater.job_queue
    job.run_repeating(check_all_services, POLLING_INTERVAL)
    dispatcher.add_handler(CommandHandler('add', add))
    dispatcher.add_handler(CommandHandler('remove', remove))
    dispatcher.add_handler(CommandHandler('list', list_services))
    dispatcher.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
