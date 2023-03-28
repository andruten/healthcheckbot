from typing import Dict, List, Optional

from models import Service, ServiceManager, ServiceStatus
from persistence import LocalJsonRepository


def chat_service_checker_command_handler(chat_id: str) -> Dict[Dict, Optional[List]]:
    persistence = LocalJsonRepository.create(chat_id)
    service_manager = ServiceManager(persistence)
    active_services = service_manager.fetch_active()
    unhealthy_services = []
    healthy_services = []
    for service in active_services:
        if service.healthcheck_backend.check() is False and service.status != ServiceStatus.UNHEALTHY:
            unhealthy_services.append(service)
            service_manager.mark_as_unhealthy(service)
        if service.status == ServiceStatus.UNHEALTHY:
            healthy_services.append(service)
            service_manager.mark_as_healthy(service)
    if unhealthy_services or healthy_services:
        return {
            chat_id: {'unhealthy': unhealthy_services, 'healthy': healthy_services}
        }
    return {}


def chat_services_checker_command_handler() -> Dict[str, Optional[Dict]]:
    chat_failing_services = {}
    chat_ids = LocalJsonRepository.get_all_chat_ids()

    for chat_id in chat_ids:
        failing_services = chat_service_checker_command_handler(chat_id)
        chat_failing_services.update(**failing_services)

    return chat_failing_services


def add_service_command_handler(chat_id, service_type, name, domain, port) -> Service:
    persistence = LocalJsonRepository.create(chat_id)
    return ServiceManager(persistence).add(service_type, name, domain, port)


def remove_services_command_handler(name, chat_id: str) -> None:
    persistence = LocalJsonRepository.create(chat_id)
    ServiceManager(persistence).remove(name)


def list_services_command_handler(chat_id: str) -> List[str]:
    persistence = LocalJsonRepository.create(chat_id)
    all_services = ServiceManager(persistence).fetch_all()
    print(all_services)
    return [f'\n{service}' for service in all_services]
