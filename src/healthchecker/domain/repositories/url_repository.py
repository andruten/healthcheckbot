from abc import ABC, abstractmethod

from healthchecker.domain.models.url import Url


class UrlRepository(ABC):
    @abstractmethod
    async def get_all_active(self) -> list[Url]: ...

    @abstractmethod
    async def get_by_id(self, url_id: int) -> Url | None: ...

    @abstractmethod
    async def add(self, url: Url) -> Url: ...

    @abstractmethod
    async def update(self, url: Url) -> Url: ...

    @abstractmethod
    async def delete(self, url_id: int) -> None: ...
