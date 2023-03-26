import json
from abc import ABC, abstractmethod
from os import listdir
from os.path import isfile, join, splitext
from typing import Dict, List


class BaseRepository(ABC):

    @classmethod
    @abstractmethod
    def create(cls, chat_id: str):
        pass

    @abstractmethod
    def fetch_all(self):
        pass

    @abstractmethod
    def add(self, data_to_append):
        pass

    @abstractmethod
    def remove(self, name: str):
        pass


class PersistenceBackend(BaseRepository):

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

    def fetch_all(self):
        try:
            with open(self.filename) as f:
                return json.load(f)
        except FileNotFoundError:
            self._save([])
            return []

    def add(self, data_to_append):
        services_data = self.fetch_all()
        services_data.append(data_to_append)
        self._save(services_data)

    def remove(self, name: str):
        services_data = [item for item in self.fetch_all() if item['name'].lower() != name.lower()]
        self._save(services_data)
