import logging
from datetime import datetime, timezone
from typing import Dict, List

from models.service import ServiceStatus, Service
from persistence import BaseRepository

logger = logging.getLogger(__name__)


class ServiceRepository:

    def __init__(self, persistence_backend: BaseRepository) -> None:
        self.persistence_backend = persistence_backend

    def update_service_status(self, service: Service, time_to_first_byte):
        service.last_time_healthy = datetime.now(timezone.utc)
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
                service_data['last_time_healthy'] = datetime.strptime(
                    service_data['last_time_healthy'],
                    '%Y-%m-%dT%H:%M:%S.%f'
                )
            except (TypeError, KeyError) as e:
                logger.debug(f'Exception occurred {e}')
            try:
                service_data['expire_date'] = datetime.strptime(
                    service_data['expire_date'],
                    '%Y-%m-%dT%H:%M:%S.%f'
                )
            except (TypeError, KeyError) as e:
                logger.debug(f'Exception occurred {e}')
            services.append(Service(status=service_status, **service_data))
        return services

    def fetch_active(self) -> List[Service]:
        return [service for service in self.fetch_all() if service.enabled is True]

    def add(self, name: str, url: str) -> Service:
        service = Service(name, url, )
        self.persistence_backend.add(service.to_dict())
        return service

    def remove(self, name) -> None:
        self.persistence_backend.remove(name)
        self.fetch_all()
