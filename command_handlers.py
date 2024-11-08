import asyncio
from datetime import datetime, timezone
import logging
from typing import Any

import httpx

from models import Service, ServiceManager, ServiceStatus
from persistence import LocalJsonRepository

logger = logging.getLogger(__name__)


transport = httpx.AsyncHTTPTransport(retries=3)
timeout = httpx.Timeout(5, read=None)


async def chat_service_checker_command_handler(chat_id: str) -> dict[str, dict[str, Any]]:
    persistence = LocalJsonRepository.create(chat_id)
    service_manager = ServiceManager(persistence)
    active_services = service_manager.fetch_active()
    unhealthy_services = []
    healthy_services = []
    time_down = {}
    backend_checks = []
    async with httpx.AsyncClient(transport=transport, timeout=timeout) as session:
        for service in active_services:
            logger.info(f'name={service.name} status={service.status.value}')
            backend_checks.append(service.healthcheck_backend.check(session))
        responses = await asyncio.gather(*backend_checks)
    services = []
    for service, (service_is_healthy, time_to_first_byte, expire_date) in zip(active_services, responses):
        if service_is_healthy is False:
            if service.status != ServiceStatus.UNHEALTHY:
                service.status = ServiceStatus.UNHEALTHY
                unhealthy_services.append(service)
        else:
            if service.status != ServiceStatus.HEALTHY:
                service.status = ServiceStatus.HEALTHY
                healthy_services.append(service)
                last_time_healthy_initial = service.last_time_healthy.replace(microsecond=0)
                now_utc = datetime.now(timezone.utc).replace(microsecond=0)
                try:
                    time_down[service.name] = now_utc - last_time_healthy_initial
                except (TypeError, AttributeError) as e:
                    logger.info(f'Couldn\'t calculate time_down in {service}: {e}')
            service.time_to_first_byte = time_to_first_byte
            service.expire_date = expire_date
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
        all_chats_fetched_services.update(**fetched_services)

    return all_chats_fetched_services


def add_service_command_handler(chat_id, service_type, name, domain, port) -> Service:
    persistence = LocalJsonRepository.create(chat_id)
    return ServiceManager(persistence).add(service_type, name, domain, port)


def remove_services_command_handler(name, chat_id: str) -> None:
    persistence = LocalJsonRepository.create(chat_id)
    ServiceManager(persistence).remove(name)


def list_services_command_handler(chat_id: str) -> str:
    persistence = LocalJsonRepository.create(chat_id)
    all_services = ServiceManager(persistence).fetch_all()
    if not all_services:
        return 'There is nothing to see here'
    result = ''
    for service in all_services:
        result += '\n\n'
        result += f'`{service.name}` is **{service.status.value}**'
        if service.status == ServiceStatus.HEALTHY and service.time_to_first_byte is not None:
            result += f'\nttfb: `{service.time_to_first_byte}`'
        elif service.status == ServiceStatus.UNHEALTHY and service.last_time_healthy is not None:
            result += f'\nLast time healthy: `{service.last_time_healthy.strftime("%d/%m/%Y %H:%M:%S")}`'
        if service.expire_date is not None:
            result += f'\nCert expires: `{service.expire_date.strftime("%d/%m/%Y %H:%M:%S")}`'
    return result
