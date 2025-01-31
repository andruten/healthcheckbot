from abc import ABC, abstractmethod
from datetime import datetime
from typing import Tuple, Optional


class BaseBackend(ABC):
    def __init__(self, service) -> None:
        self.service = service

    @abstractmethod
    async def check(self, *args, **kwargs) -> Tuple[bool, Optional[float], Optional[datetime], Optional[int]]:  # pragma: no cover
        pass
