from healthchecker.domain.models.url import Url
from healthchecker.domain.repositories.url_repository import UrlRepository


class ManageUrlsUseCase:
    def __init__(self, url_repo: UrlRepository):
        self._url_repo = url_repo

    async def add(
        self, url: str, name: str | None = None, alert_before_days: int = 30
    ) -> Url:
        domain_url = Url.create(url=url, name=name, alert_before_days=alert_before_days)
        return await self._url_repo.add(domain_url)

    async def list_all(self) -> list[Url]:
        return await self._url_repo.get_all_active()

    async def delete(self, url_id: int) -> None:
        await self._url_repo.delete(url_id)

    async def get_by_id(self, url_id: int) -> Url | None:
        return await self._url_repo.get_by_id(url_id)
