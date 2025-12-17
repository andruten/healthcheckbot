from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ServiceFetchResponse:
    service_is_healthy: bool = False
    elapsed_total_seconds: Optional[float] = None
    expire_date: Optional[datetime] = None
    status_code: Optional[int] = None
