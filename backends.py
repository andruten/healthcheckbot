from abc import ABC, abstractmethod
import logging
from datetime import datetime
from socket import AF_INET, SOCK_STREAM, error, socket, timeout
from typing import Tuple, Optional

import httpx

logger = logging.getLogger(__name__)


class BaseBackend(ABC):
    def __init__(self, service) -> None:
        self.service = service

    @abstractmethod
    async def check(self, *args, **kwargs) -> Tuple[bool, Optional[float], Optional[datetime]]:  # pragma: no cover
        pass


class SocketBackend(BaseBackend):
    def check(self) -> Tuple[bool, Optional[float], Optional[datetime]]:
        a_socket = socket(AF_INET, SOCK_STREAM)
        location = (self.service.domain, self.service.port)
        try:
            result_of_check = a_socket.connect_ex(location)
        except (error, timeout):
            return False, None, None
        else:
            a_socket.close()
        return result_of_check == 0, None, None


class RequestBackend(BaseBackend):
    def _get_url(self) -> str:
        protocol = 'https' if self.service.port == 443 else 'http'
        return f'{protocol}://{self.service.domain}'

    async def check(self, session) -> Tuple[bool, Optional[float], Optional[datetime]]:
        url = self._get_url()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        try:
            logger.debug(f"Fetching {url}")
            response = await session.request(method='GET', url=url, headers=headers)
        except httpx.HTTPError as exc:
            logger.warning(f'"{url}" request failed {exc}')
            return False, None, None
        else:
            raw_stream = response.extensions['network_stream']
            ssl_object = raw_stream.get_extra_info('ssl_object')
            cert = ssl_object.getpeercert()
            expire_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            elapsed_total_seconds = response.elapsed.total_seconds()
            logger.debug(f'{url} fetched in {elapsed_total_seconds}')
            service_is_healthy = (500 <= response.status_code <= 511)
            return not service_is_healthy, elapsed_total_seconds, expire_date
