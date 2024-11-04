import json
import logging
from abc import ABC, abstractmethod
from json import JSONDecodeError
from os import listdir
from os.path import isfile, join, splitext
from typing import Dict, List

logger = logging.getLogger(__name__)


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


class LocalJsonRepository(BaseRepository):

    def __init__(self, chat_id: str, filename: str) -> None:
        self.chat_id = chat_id
        self.filename = filename

    @staticmethod
    def get_all_chat_ids(path='data'):
        json_filenames = [filename for filename in listdir(path)
                          if isfile(join(path, filename)) and filename.endswith('.json')]
        return [splitext(filename)[0] for filename in json_filenames]

    @classmethod
    def create(cls, chat_id: str):
        filename = f'data/{chat_id}.json'
        return cls(chat_id, filename)

    def _save(self, data: List[Dict]):
        with open(self.filename, '+w') as f:
            f.write(json.dumps(data))

    def _initialize_data(self) -> None:
        self._save([])

    def fetch_all(self):
        try:
            with open(self.filename) as f:
                return json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            logging.warning('JSON file did not exist or it was empty. Creating and setting an empty JSON list')
            self._initialize_data()
            return self.fetch_all()

    def add(self, data_to_append: Dict):
        services_data = self.fetch_all()
        services_data.append(data_to_append)
        self._save(services_data)

    def remove(self, name: str):
        services_data = [item for item in self.fetch_all() if item['name'].lower() != name.lower()]
        self._save(services_data)

    def bulk_update(self, services_to_update: List[Dict]):
        self._save(services_to_update)

    def update(self, service_to_update: Dict):
        all_services = self.fetch_all()
        for index, service in enumerate(all_services):
            if service['name'].lower() == service_to_update['name'].lower():
                all_services[index] = service_to_update
                break
        self._save(all_services)
