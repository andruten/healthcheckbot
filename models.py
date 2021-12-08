from typing import List, Dict

from backends import BaseBackend, SocketBackend, RequestBackend
from persistence import PersistenceBackend


class Service:
    HEALTHCHECK_BACKENDS = {
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
    def healthcheck_backend(self) -> BaseBackend:
        return self.HEALTHCHECK_BACKENDS[self.service_type](self)

    def __repr__(self) -> str:
        return f'{self.name} <{self.domain}:{self.port}>'

    def __str__(self) -> str:
        return f'{self.name} <{self.domain}:{self.port}>'

    def to_dict(self) -> Dict:
        return self.__dict__


class ServiceManager:

    def __init__(self, persistence_backend: PersistenceBackend) -> None:
        self.persistence_backend = persistence_backend

    def fetch_all(self) -> List[Service]:
        services = []
        for service_data in self.persistence_backend.fetch_all():
            services.append(Service(**service_data))
        return services

    def fetch_active(self) -> List[Service]:
        return [service for service in self.fetch_all() if service.enabled is True]

    def add(self, service_type: str, name: str, domain: str, port: int, enabled: bool = True) -> Service:
        service = Service(service_type.lower(), name, domain, int(port), enabled)
        self.persistence_backend.add(service.to_dict())
        return service

    def remove(self, name) -> None:
        self.persistence_backend.remove(name)
        self.fetch_all()
