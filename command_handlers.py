from datetime import datetime
import logging
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
        last_time_healthy_initial = service.last_time_healthy
        service_is_healthy, time_to_first_byte = service.healthcheck_backend.check()
        if service_is_healthy is False:
            if service.status != ServiceStatus.UNHEALTHY:
                unhealthy_services.append(service)
                service_manager.mark_as_unhealthy(service)
        else:
            if service.status != ServiceStatus.HEALTHY:
                healthy_services.append(service)
                try:
                    time_down[service.name] = (
                        datetime.utcnow().replace(microsecond=0) - last_time_healthy_initial.replace(microsecond=0)
                    )
                except (TypeError, AttributeError) as e:
                    logger.info(f'Something happened while calculating time_down: {e}')
                service_manager.mark_as_healthy(service)
            service_manager.update_service_status(service, time_to_first_byte)
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


def list_services_command_handler(chat_id: str) -> str:
    persistence = LocalJsonRepository.create(chat_id)
    all_services = ServiceManager(persistence).fetch_all()
    if not all_services:
        return 'There is nothing to see here'
    result = ''
    for service in all_services:
        result += '\n\n'
        result += f'name: `{service.name}`\n'
        result += f'status: `{service.status.value}`'
        if service.status == ServiceStatus.HEALTHY and service.time_to_first_byte is not None:
            result += f'\nresponse time: `{service.time_to_first_byte}`'
        elif service.status == ServiceStatus.UNHEALTHY and service.last_time_healthy is not None:
            result += f'\nlast time healthy: `{service.last_time_healthy.strftime("%m/%d/%Y %H:%M:%S")}`'
    return result
