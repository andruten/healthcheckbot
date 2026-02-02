import asyncio
from datetime import datetime, timezone
import logging
from typing import Any

import httpx

from models import Service, ServiceStatus
from repositories import ServiceRepository
from persistence import LocalJsonRepository

logger = logging.getLogger(__name__)


transport = httpx.AsyncHTTPTransport(retries=1)
timeout = httpx.Timeout(5, read=None)


async def chat_service_checker_command_handler(chat_id: str) -> dict[str, dict[str, Any]]:
    persistence = LocalJsonRepository.create(chat_id)
    service_manager = ServiceRepository(persistence)
    active_services = service_manager.fetch_active()
    unhealthy_services = []
    healthy_services = []
    time_down = {}
    backend_checks = []
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None).replace(microsecond=0)
    async with httpx.AsyncClient(transport=transport, timeout=timeout) as session:
        for service in active_services:
            logger.debug(f'name={service.name} status={service.status.value}')
            backend_checks.append(service.healthcheck_backend.check(session))
        responses = await asyncio.gather(*backend_checks)
    services = []
    for service, response in zip(active_services, responses):
        initial_service_status = service.status
        service.last_http_response_status_code = response.status_code
        if response.service_is_healthy is False:
            if response.expire_date:
                service.status = (
                    ServiceStatus.UNHEALTHY if response.expire_date > now_utc else ServiceStatus.CERT_EXPIRED
                )
            else:
                service.status = ServiceStatus.UNHEALTHY

            if initial_service_status not in ServiceStatus.unhealthy_statuses:
                unhealthy_services.append(service)
        else:
            service.status = ServiceStatus.HEALTHY
            if initial_service_status != ServiceStatus.HEALTHY:
                healthy_services.append(service)
                last_time_healthy_initial = service.last_time_healthy
                try:
                    time_down[service.name] = (
                        now_utc - last_time_healthy_initial.replace(microsecond=0)
                    )
                except (TypeError, AttributeError) as e:
                    logger.warning(f"Couldn't calculate time_down in {service}: {e}")
            service.last_time_healthy = now_utc
            service.time_to_first_byte = response.elapsed_total_seconds
            service.expire_date = response.expire_date
            service.last_http_response_status_code = response.status_code
        services.append(service.to_dict())
    service_manager.update(services)

    if unhealthy_services or healthy_services:
        return {
            chat_id: {
                'unhealthy': unhealthy_services,
                'healthy': healthy_services,
                'time_down': {**time_down},
            }
        }
    return {}


async def chat_services_checker_command_handler() -> dict[str, dict]:
    all_chats_fetched_services = {}
    chat_ids = LocalJsonRepository.get_all_chat_ids()

    for chat_id in chat_ids:
        fetched_services = await chat_service_checker_command_handler(chat_id)
        logger.info(f'Fetched services for chat {chat_id}: {fetched_services}')
        all_chats_fetched_services.update(**fetched_services)

    return all_chats_fetched_services


def add_service_command_handler(chat_id, name, url) -> Service:
    persistence = LocalJsonRepository.create(chat_id)
    return ServiceRepository(persistence).add(name, url)


def remove_services_command_handler(name, chat_id: str) -> None:
    persistence = LocalJsonRepository.create(chat_id)
    ServiceRepository(persistence).remove(name)
    logger.info(f'Removed service {name} from chat {chat_id}')


def list_services_command_handler(chat_id: str) -> str:
    persistence = LocalJsonRepository.create(chat_id)
    all_services = ServiceRepository(persistence).fetch_all()
    if not all_services:
        return 'There is nothing to see here'
    result = ''
    for service in all_services:
        result += '\n\n'
        result += f'`{service.name}` is **{service.status.value.upper()}**'
        result += f'\nStatus: `{service.last_http_response_status_code}`'
        if service.status == ServiceStatus.HEALTHY and service.time_to_first_byte is not None:
            result += f'\nttfb: `{service.time_to_first_byte}`'
        elif service.status in ServiceStatus.unhealthy_statuses and service.last_time_healthy is not None:
            result += f'\nLast time healthy: `{service.last_time_healthy.strftime("%d/%m/%Y %H:%M:%S")}`'
        if service.expire_date is not None:
            if service.status == ServiceStatus.CERT_EXPIRED:
                result += f'\nCert expired: `{service.expire_date.strftime("%d/%m/%Y %H:%M:%S")}`'
            else:
                result += f'\nCert expires: `{service.expire_date.strftime("%d/%m/%Y %H:%M:%S")}`'
    return result
