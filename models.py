from typing import List

from backends import SocketBackend, RequestBackend
from persistence import read_services, add_service, remove_service


class Service:
    BACKENDS = {
        'socket': SocketBackend,
        'request': RequestBackend,
    }

    def __init__(self, service_type: str, name: str, domain: str, port: int, enabled: bool = True) -> None:
        self.service_type = service_type
        self.name = name
        self.domain = domain
        self.port = port
        self.enabled = enabled

    @property
    def backend(self):
        return self.BACKENDS[self.service_type](self)

    def __repr__(self) -> str:
        return f'{self.name} <{self.domain}:{self.port}>'

    def to_dict(self):
        return self.__dict__


class ServiceManager:

    def fetch_all(self) -> List[Service]:
        services = []
        for service_data in read_services():
            services.append(Service(**service_data))
        return services

    def fetch_active(self) -> List[Service]:
        return [service for service in self.fetch_all() if service.enabled is True]

    def add(self, service_type: str, name: str, domain: str, port: int, enabled: bool = True) -> Service:
        service = Service(service_type.lower(), name, domain, int(port), enabled)
        add_service(service.to_dict())
        return service

    def remove(self, name):
        remove_service(name)
        self.fetch_all()
