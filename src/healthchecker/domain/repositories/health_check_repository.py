from abc import ABC, abstractmethod
from datetime import date

from healthchecker.domain.models.health_check import HealthCheck


class HealthCheckRepository(ABC):
    @abstractmethod
    async def save(self, check: HealthCheck) -> HealthCheck: ...

    @abstractmethod
    async def get_by_url_id(
        self, url_id: int, limit: int = 10
    ) -> list[HealthCheck]: ...

    @abstractmethod
    async def get_latest_by_url_id(self, url_id: int) -> HealthCheck | None: ...

    @abstractmethod
    async def get_dates_needing_consolidation(
        self, cutoff_date: date
    ) -> list[tuple[int, date]]: ...

    @abstractmethod
    async def get_raw_for_date(
        self, url_id: int, target_date: date
    ) -> list[HealthCheck]: ...

    @abstractmethod
    async def purge_older_than(self, cutoff_date: date) -> int: ...
