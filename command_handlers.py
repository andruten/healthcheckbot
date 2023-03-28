from typing import Dict, List, Optional

from models import Service, ServiceManager
from persistence import LocalJsonRepository


def chat_service_checker_command_handler(chat_id: str) -> Dict[str, Optional[List]]:
    persistence = LocalJsonRepository.create(chat_id)
    failing_active_services = ServiceManager(persistence).fetch_active()
    failing_services = []
    for service in failing_active_services:
        service_response = service.healthcheck_backend.check()
        if not service_response:
            failing_services.append(service)
    if failing_services:
        return {
            chat_id: failing_services
        }
    return {}


def chat_services_checker_command_handler() -> Dict[str, Optional[List]]:
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
    return [f'\n{service}' for service in all_services]
