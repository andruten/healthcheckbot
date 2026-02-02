import logging
from datetime import datetime, timedelta, timezone

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from commands.handlers import chat_services_checker_command_handler
from models import Service

logger = logging.getLogger(__name__)

# Expiration warning thresholds
CERT_WARNING_DAYS = [7, 1]


def _format_unhealthy_message(service: Service) -> str:
    """Format notification message for an unhealthy service."""
    status_text = '**certificate is expired**' if service.is_cert_expired else '**is down**'
    response_code = service.last_http_response_status_code or "nothing"
    return (
        f'🤕 `{service.name}` {status_text}!'
        f'\nIt returned `{response_code}`'
    )


def _format_healthy_message(service: Service, time_down: str | None = None) -> str:
    """Format notification message for a recovered service."""
    suffix = f' after {time_down}' if time_down else ''
    return (
        f'✅ `{service.name}` is back to normal{suffix}!'
        f'\nIt returned `{service.last_http_response_status_code}`'
    )


def _format_cert_expiring_message(service: Service, days_left: int) -> str:
    """Format warning message for an expiring certificate."""
    urgency = '🚨' if days_left <= 1 else '⚠️'
    time_desc = 'tomorrow' if days_left == 1 else f'in {days_left} days'
    expire_date_str = service.expire_date.strftime('%Y-%m-%d %H:%M:%S UTC')

    return (
        f'{urgency} `{service.name}` certificate expires {time_desc}!'
        f'\nExpiration date: `{expire_date_str}`'
    )


def _get_days_until_expiration(expire_date: datetime) -> int | None:
    """Calculate days until certificate expiration."""
    if not expire_date:
        return None

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    # Ensure expire_date is naive (no timezone) for comparison
    expire_naive = expire_date.replace(tzinfo=None) if expire_date.tzinfo else expire_date

    days_left = (expire_naive - now_utc).days
    return days_left if days_left >= 0 else None


def _should_warn_about_expiration(service: Service) -> int | None:
    """
    Check if a warning should be sent for certificate expiration.
    Returns the number of days left if warning threshold is hit, None otherwise.
    """
    if not service.expire_date or service.is_cert_expired:
        return None

    days_left = _get_days_until_expiration(service.expire_date)

    if days_left is None:
        return None

    # Check if we should send a warning for this threshold
    if days_left in CERT_WARNING_DAYS:
        return days_left

    return None


def _get_downtime_suffix(fetched_services: dict, service_name: str) -> str:
    """Extract downtime information for a service, if available."""
    try:
        return fetched_services['time_down'][service_name]
    except (KeyError, TypeError) as e:
        logger.debug(f'No downtime information for {service_name}: {e}')
        return ''


async def _send_service_notifications(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: str,
    fetched_services: dict[str, list[Service]]
) -> None:
    """Send notifications for all services in a chat."""
    # Notify about unhealthy services
    for service in fetched_services['unhealthy']:
        message = _format_unhealthy_message(service)
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )

    # Notify about recovered services
    for service in fetched_services['healthy']:
        print(service)
        time_down = _get_downtime_suffix(fetched_services, service.name)
        message = _format_healthy_message(service, time_down)
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )


async def _send_cert_expiration_warnings(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: str,
    services: list[Service],
) -> None:
    """Send warnings for certificates that are about to expire."""
    for service in services:
        days_left = _should_warn_about_expiration(service)
        if days_left is not None:
            message = _format_cert_expiring_message(service, days_left)
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f'Sent certificate expiration warning for {service.name}: {days_left} days left')


async def check_all_services(context: ContextTypes.DEFAULT_TYPE):
    """Check all services and send notifications to respective chats."""
    chat_fetched_services = await chat_services_checker_command_handler()

    for chat_id, fetched_services in chat_fetched_services.items():
        # Send status change notifications (up/down)
        logger.info(f'Sending notifications for chat {chat_id}')
        await _send_service_notifications(context, chat_id, fetched_services)

        # Check for expiring certificates across all services
        all_services = fetched_services.get('unhealthy', []) + fetched_services.get('healthy', [])
        logger.info(f'Checking for expiring certificates for {len(all_services)} services')
        await _send_cert_expiration_warnings(context, chat_id, all_services)
