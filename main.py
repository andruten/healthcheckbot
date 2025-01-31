import logging
import os

import environ
from telegram.ext import ApplicationBuilder, CommandHandler

from commands import check_all_services, list_services, remove_service, add_service, error
from filter_allowed_chats import FilterAllowedChats

abspath = os.path.abspath(__file__)
directory_name = os.path.dirname(abspath)
os.chdir(directory_name)

env = environ.Env()
environ.Env.read_env()

ALLOWED_CHAT_IDS = env.list('ALLOWED_CHAT_IDS', default=[])
BOT_TOKEN = env.str('BOT_TOKEN')
POLLING_INTERVAL = env.int('POLLING_INTERVAL', 60)
LOG_LEVEL = logging.DEBUG if env.str('LOG_LEVEL') == 'DEBUG' else logging.INFO

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=LOG_LEVEL)

logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    filter_allowed_chats = FilterAllowedChats(ALLOWED_CHAT_IDS)

    job_queue = app.job_queue
    job_queue.run_repeating(check_all_services, POLLING_INTERVAL, first=1)

    add_command_handler = CommandHandler('add', add_service, filter_allowed_chats)
    remove_command_handler = CommandHandler('remove', remove_service, filter_allowed_chats)
    list_command_handler = CommandHandler('list', list_services, filter_allowed_chats)

    app.add_handler(add_command_handler)
    app.add_handler(remove_command_handler)
    app.add_handler(list_command_handler)

    app.add_error_handler(error)

    app.run_polling()


if __name__ == '__main__':
    main()
