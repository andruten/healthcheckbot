import datetime
import logging
import time
from typing import Dict, List, Optional

from models import Service, ServiceManager, ServiceStatus
from persistence import LocalJsonRepository

logger = logging.getLogger(__name__)


def chat_service_checker_command_handler(chat_id: str) -> Dict[Dict, Optional[List]]:
    persistence = LocalJsonRepository.create(chat_id)
    service_manager = ServiceManager(persistence)
    active_services = service_manager.fetch_active()
    unhealthy_services = []
    healthy_services = []
    time_down = {}
    for service in active_services:
        logger.info(f'name={service.name} status={service.status}')
        start = time.time()
        last_time_healthy_initial = service.last_time_healthy
        service_is_healthy: bool = service.healthcheck_backend.check()
        time_to_first_byte = time.time() - start
        if service_is_healthy is False:
            if service.status != ServiceStatus.UNHEALTHY:
                unhealthy_services.append(service)
                service_manager.mark_as_unhealthy(service)
        else:
            if service.status != ServiceStatus.HEALTHY:
                healthy_services.append(service)
                try:
                    time_down[service.name] = datetime.datetime.utcnow() - last_time_healthy_initial
                except TypeError:
                    pass
                service_manager.mark_as_healthy(service, time_to_first_byte)
    if unhealthy_services or healthy_services:
        return {
            chat_id: {'unhealthy': unhealthy_services, 'healthy': healthy_services, 'time_down': {**time_down}}
        }
    return {}


def chat_services_checker_command_handler() -> Dict[str, Optional[Dict]]:
    all_chats_fetched_services = {}
    chat_ids = LocalJsonRepository.get_all_chat_ids()

    for chat_id in chat_ids:
        fetched_services = chat_service_checker_command_handler(chat_id)
        all_chats_fetched_services.update(**fetched_services)

    return all_chats_fetched_services


def add_service_command_handler(chat_id, service_type, name, domain, port) -> Service:
    persistence = LocalJsonRepository.create(chat_id)
    return ServiceManager(persistence).add(service_type, name, domain, port)


def remove_services_command_handler(name, chat_id: str) -> None:
    persistence = LocalJsonRepository.create(chat_id)
    ServiceManager(persistence).remove(name)


def list_services_command_handler(chat_id: str) -> List[str]:
    persistence = LocalJsonRepository.create(chat_id)
    all_services = ServiceManager(persistence).fetch_all()
    if not all_services:
        return ['I\'m polling nothing']
    return [f'\n\n*{service.name}* \n`{service.status.value}`\nTTFB: {service.time_to_first_byte:.2f}'
            for service in all_services]
