import enum
from dataclasses import asdict, dataclass, field
from typing import Dict, List

from backends import BaseBackend, RequestBackend, SocketBackend
from persistence import BaseRepository

HEALTHCHECK_BACKENDS = {
    'socket': SocketBackend,
    'request': RequestBackend,
}


class ServiceStatus(enum.Enum):
    UNKNOWN = 'unknown'
    HEALTHY = 'healthy'
    UNHEALTHY = 'unhealthy'


def service_asdict_factory(data):

    def convert_value(obj):
        if isinstance(obj, ServiceStatus):
            return obj.value
        return obj

    return dict((k, convert_value(v)) for k, v in data)


@dataclass
class Service:
    service_type: str = field()
    name: str = field()
    domain: str = field()
    port: int = field()
    enabled: bool = True
    status: ServiceStatus = ServiceStatus.UNKNOWN

    @property
    def healthcheck_backend(self) -> BaseBackend:
        return HEALTHCHECK_BACKENDS[self.service_type](self)

    def __repr__(self) -> str:
        return f'{self.name} <{self.domain}:{self.port}>'

    def __str__(self) -> str:
        return f'{self.name} <{self.domain}:{self.port}>'

    def to_dict(self) -> Dict:
        return asdict(self, dict_factory=service_asdict_factory)


class ServiceManager:

    def __init__(self, persistence_backend: BaseRepository) -> None:
        self.persistence_backend = persistence_backend

    def mark_as_healthy(self, service: Service):
        service.status = ServiceStatus.HEALTHY
        self.persistence_backend.update(service.to_dict())

    def mark_as_unhealthy(self, service: Service):
        service.status = ServiceStatus.UNHEALTHY
        self.persistence_backend.update(service.to_dict())

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
