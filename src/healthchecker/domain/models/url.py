from dataclasses import dataclass
from datetime import datetime, UTC


@dataclass
class Url:
    id: int | None
    name: str
    url: str
    alert_before_days: int
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None

    @classmethod
    def create(
        cls, url: str, name: str | None = None, alert_before_days: int = 30
    ) -> "Url":
        now = datetime.now(UTC)
        return cls(
            id=None,
            name=name or url,
            url=url,
            alert_before_days=alert_before_days,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
