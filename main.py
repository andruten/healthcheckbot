import logging
import os
import socket
import requests
from dotenv import load_dotenv
from telegram.ext import Updater, CallbackContext

from models import Service
from persistence import read_services

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
    services = read_services()
    failing_services = []
    for service_data in services:
        service = Service(**service_data)
        if not service.enabled:
            continue
        service_response = service.backend.check()
        if not service_response:
            failing_services.append(service)
    if failing_services:
        for failing_service in failing_services:
            text = f'{failing_service} is down!'
            context.bot.send_message(chat_id=CHAT_ID, text=text)


def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    job = updater.job_queue
    job.run_repeating(check_all_services, POLLING_INTERVAL)
    dispatcher.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
