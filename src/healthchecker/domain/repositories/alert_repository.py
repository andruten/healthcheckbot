from abc import ABC, abstractmethod

from healthchecker.domain.models.alert import Alert


class AlertRepository(ABC):
    @abstractmethod
    async def save(self, alert: Alert) -> Alert: ...

    @abstractmethod
    async def get_unsent(self) -> list[Alert]: ...

    @abstractmethod
    async def mark_as_sent(self, alert_id: int) -> None: ...
