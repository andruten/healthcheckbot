from healthchecker.domain.models.url import Url
from healthchecker.domain.repositories.url_repository import (
    UrlRepository as UrlRepositoryInterface,
)
from healthchecker.infrastructure.persistence.tortoise_models import UrlModel


class TortoiseUrlRepository(UrlRepositoryInterface):
    async def get_all_active(self) -> list[Url]:
        rows = await UrlModel.filter(is_active=True).order_by("id")
        return [self._to_domain(r) for r in rows]

    async def get_by_id(self, url_id: int) -> Url | None:
        row = await UrlModel.get_or_none(id=url_id)
        return self._to_domain(row) if row else None

    async def add(self, url: Url) -> Url:
        row = await UrlModel.create(
            name=url.name,
            url=url.url,
            alert_before_days=url.alert_before_days,
            is_active=url.is_active,
        )
        return self._to_domain(row)

    async def update(self, url: Url) -> Url:
        await UrlModel.filter(id=url.id).update(
            name=url.name,
            url=url.url,
            alert_before_days=url.alert_before_days,
            is_active=url.is_active,
        )
        return url

    async def delete(self, url_id: int) -> None:
        await UrlModel.filter(id=url_id).delete()

    @staticmethod
    def _to_domain(row: UrlModel) -> Url:
        return Url(
            id=row.id,
            name=row.name,
            url=row.url,
            alert_before_days=row.alert_before_days,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
