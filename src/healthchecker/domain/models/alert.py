from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AlertType(str, Enum):
    SSL_EXPIRY = "ssl_expiry"
    HTTP_DOWN = "http_down"
    HTTP_UP = "http_up"


@dataclass
class Alert:
    id: int | None
    url_id: int
    alert_type: AlertType
    message: str
    is_sent: bool
    created_at: datetime
