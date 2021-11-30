import logging
import os
import socket
import requests
from dotenv import load_dotenv
from telegram.ext import Updater, CallbackContext
from persistence import read_services

# Enable logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

load_dotenv()

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


def check_socket_connection(domain: str, port: int, **kwargs) -> bool:
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    location = (domain, port)
    result_of_check = a_socket.connect_ex(location)
    return bool(result_of_check == 0)


def check_request_connection(domain: str, port: int, timeout: int = 3, **kwargs) -> bool:
    protocol = 'https' if port == 443 else 'http'
    url = f'{protocol}://{domain}:{port}'
    try:
        response = requests.head(url, timeout=timeout)
    except requests.exceptions.RequestException:
        return False
    else:
        if response.status_code >= 400:
            return True
    return True


CONNECTIONS = {
    'socket': check_socket_connection,
    'request': check_request_connection,
}


def check_all_services(context: CallbackContext):
    services = read_services()
    failing_services = []
    for service in services:
        enabled = service.pop('enabled', False)
        if not enabled:
            continue
        service_type = service.pop('service_type')
        # Name is not used (for now)
        service_response = CONNECTIONS[service_type](**service)
        if not service_response:
            failing_services.append(service)
    if failing_services:
        for failing_service in failing_services:
            text = f'{failing_service["name"]} is down <{failing_service["domain"]}:{failing_service["port"]}>'
            context.bot.send_message(chat_id=CHAT_ID, text=text)


def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    job = updater.job_queue
    job.run_repeating(check_all_services, POLLING_INTERVAL)
    dispatcher.add_error_handler(error)
    updater.bot.sendMessage(chat_id=CHAT_ID, text='Hola buenas tardes!')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
