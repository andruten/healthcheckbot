import datetime
import enum
from dataclasses import asdict, dataclass, field
import logging
from datetime import timezone
from typing import Dict, List, Optional

from backends import BaseBackend, RequestBackend, SocketBackend
from persistence import BaseRepository

logger = logging.getLogger(__name__)

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
        elif isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S.%f')
        return obj

    return dict((k, convert_value(v)) for k, v in data)


@dataclass
class Service:
    service_type: str = field()
    name: str = field()
    domain: str = field()
    port: int = field()
    enabled: bool = field(default=True)
    last_time_healthy: Optional[datetime.datetime] = field(default=None)
    time_to_first_byte: float = field(default=0.0)
    status: ServiceStatus = field(init=True, default=ServiceStatus.UNKNOWN)

    @property
    def healthcheck_backend(self) -> BaseBackend:
        return HEALTHCHECK_BACKENDS[self.service_type](self)

    def __repr__(self) -> str:  # pragma: no cover
        return f'{self.name} <{self.domain}:{self.port}>'

    def __str__(self) -> str:  # pragma: no cover
        return f'{self.name} <{self.domain}>'

    def to_dict(self) -> Dict:
        return asdict(self, dict_factory=service_asdict_factory)


class ServiceManager:

    def __init__(self, persistence_backend: BaseRepository) -> None:
        self.persistence_backend = persistence_backend

    def update_service_status(self, service: Service, time_to_first_byte):
        service.last_time_healthy = datetime.datetime.now(timezone.utc)
        service.time_to_first_byte = time_to_first_byte
        self.persistence_backend.update(service.to_dict())

    def mark_as_healthy(self, service: Service):
        service.status = ServiceStatus.HEALTHY
        self.persistence_backend.update(service.to_dict())

    def mark_as_unhealthy(self, service: Service):
        service.status = ServiceStatus.UNHEALTHY
        self.persistence_backend.update(service.to_dict())

    def update(self, services: List[Dict]):
        self.persistence_backend.bulk_update(services)

    def fetch_all(self) -> List[Service]:
        services = []
        for service_data in self.persistence_backend.fetch_all():
            status = service_data.pop('status')
            service_status = ServiceStatus(status)
            try:
                service_data['last_time_healthy'] = datetime.datetime.strptime(
                    service_data['last_time_healthy'],
                    '%Y-%m-%dT%H:%M:%S.%f'
                )
            except (TypeError, KeyError) as e:
                logger.debug(f'Exception occurred {e}')
            services.append(Service(status=service_status, **service_data))
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
