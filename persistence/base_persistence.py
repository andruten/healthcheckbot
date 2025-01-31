from abc import ABC, abstractmethod
from typing import Dict, List


class BaseRepository(ABC):

    @classmethod
    @abstractmethod
    def create(cls, chat_id: str):  # pragma: no cover
        pass

    @abstractmethod
    def fetch_all(self):  # pragma: no cover
        pass

    @abstractmethod
    def add(self, data_to_append: Dict):  # pragma: no cover
        pass

    @abstractmethod
    def remove(self, name: str):  # pragma: no cover
        pass

    @abstractmethod
    def update(self, service_to_update: Dict):  # pragma: no cover
        pass

    @abstractmethod
    def bulk_update(self, services_to_update: List[Dict]):  # pragma: no cover
        pass
