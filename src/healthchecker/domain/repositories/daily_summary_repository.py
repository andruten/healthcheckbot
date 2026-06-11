from abc import ABC, abstractmethod
from datetime import date

from healthchecker.domain.models.daily_summary import DailySummary


class DailySummaryRepository(ABC):
    @abstractmethod
    async def save(self, summary: DailySummary) -> DailySummary: ...

    @abstractmethod
    async def get_by_url_id_and_date(
        self, url_id: int, summary_date: date
    ) -> DailySummary | None: ...

    @abstractmethod
    async def get_by_url_id(
        self, url_id: int, limit: int = 10, offset: int = 0
    ) -> list[DailySummary]: ...

    @abstractmethod
    async def exists_for_date(self, url_id: int, summary_date: date) -> bool: ...
