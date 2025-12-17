import logging

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from commands.handlers import chat_services_checker_command_handler
from models import Service

logger = logging.getLogger(__name__)


async def check_all_services(context: ContextTypes.DEFAULT_TYPE):
    chat_fetched_services = await chat_services_checker_command_handler()

    for chat_id in chat_fetched_services:
        fetched_services: dict[str, list[Service]] = chat_fetched_services[chat_id]
        unhealthy_service: Service
        for unhealthy_service in fetched_services['unhealthy']:
            status_text = '**certificate is expired**' if unhealthy_service.is_cert_expired else '**is down**'
            text = (
                f'🤕 `{unhealthy_service.name}` {status_text}!'
                f'\nIt returned `{unhealthy_service.last_http_response_status_code or "nothing"}`'
            )
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
        healthy_service: Service
        for healthy_service in fetched_services['healthy']:
            try:
                time_down = fetched_services['time_down'][healthy_service.name]
                suffix = f' after {time_down}'
            except (KeyError, TypeError) as e:
                logger.debug(f'Exception occurred: {e}')
                suffix = ''
            text = (
                f'✅ `{healthy_service.name}` is back to normal{suffix}!'
                f'\nIt returned `{healthy_service.last_http_response_status_code}`'
            )
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
