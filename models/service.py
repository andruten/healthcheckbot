import enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict

from backends import RequestBackend


class ServiceStatus(enum.Enum):
    UNKNOWN = 'unknown'
    HEALTHY = 'healthy'
    UNHEALTHY = 'unhealthy'


def service_asdict_factory(data):
    def convert_value(obj):
        if isinstance(obj, ServiceStatus):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S.%f')
        return obj

    return dict((k, convert_value(v)) for k, v in data)


@dataclass
class Service:
    name: str = field()
    url: str = field()
    enabled: bool = field(default=True)
    last_time_healthy: Optional[datetime] = field(default=None)
    last_http_response_status_code: Optional[int] = field(default=None)
    time_to_first_byte: float = field(default=0.0)
    status: ServiceStatus = field(init=True, default=ServiceStatus.UNKNOWN)
    expire_date: Optional[datetime] = field(default=None)

    @property
    def healthcheck_backend(self) -> RequestBackend:
        return RequestBackend(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f'{self.name} <{self.url}>'

    def __str__(self) -> str:  # pragma: no cover
        return f'{self.name} <{self.url}>'

    def to_dict(self) -> Dict:
        return asdict(self, dict_factory=service_asdict_factory)
