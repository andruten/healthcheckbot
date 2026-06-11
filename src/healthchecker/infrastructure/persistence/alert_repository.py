from healthchecker.domain.models.alert import Alert, AlertType
from healthchecker.domain.repositories.alert_repository import (
    AlertRepository as AlertRepositoryInterface,
)
from healthchecker.infrastructure.persistence.tortoise_models import AlertModel


class TortoiseAlertRepository(AlertRepositoryInterface):
    async def save(self, alert: Alert) -> Alert:
        row = await AlertModel.create(
            url_id=alert.url_id,
            alert_type=alert.alert_type.value,
            message=alert.message,
            is_sent=alert.is_sent,
            created_at=alert.created_at,
        )
        alert.id = row.id
        return alert

    async def get_unsent(self) -> list[Alert]:
        rows = await AlertModel.filter(is_sent=False).order_by("created_at")
        return [self._to_domain(r) for r in rows]

    async def mark_as_sent(self, alert_id: int) -> None:
        await AlertModel.filter(id=alert_id).update(is_sent=True)

    @staticmethod
    def _to_domain(row: AlertModel) -> Alert:
        return Alert(
            id=row.id,
            url_id=row.url_id,
            alert_type=AlertType(row.alert_type),
            message=row.message,
            is_sent=row.is_sent,
            created_at=row.created_at,
        )
