import logging
from datetime import datetime
from typing import Tuple, Optional

import httpx
import ssl

from .base_backend import BaseBackend

logger = logging.getLogger(__name__)


class RequestBackend(BaseBackend):
    async def check(self, session) -> Tuple[bool, Optional[float], Optional[datetime], Optional[int]]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        try:
            logger.debug(f"Fetching {self.service.url}")
            response = await session.request(method='GET', url=self.service.url, headers=headers)
        except (httpx.HTTPError, ssl.SSLCertVerificationError,) as exc:
            logger.warning(f'"{self.service.url}" request failed {exc}')
            return False, None, None, None
        else:
            raw_stream = response.extensions['network_stream']
            ssl_object = raw_stream.get_extra_info('ssl_object')
            cert = ssl_object.getpeercert()
            expire_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            elapsed_total_seconds = response.elapsed.total_seconds()
            logger.debug(f'{self.service.url} fetched in {elapsed_total_seconds}')
            service_is_healthy = (400 <= response.status_code <= 511)
            return not service_is_healthy, elapsed_total_seconds, expire_date, response.status_code
