from abc import ABC, abstractmethod
import logging
from socket import AF_INET, SOCK_STREAM, error, socket, timeout
from typing import Tuple, Optional

import requests

logger = logging.getLogger(__name__)


class BaseBackend(ABC):
    def __init__(self, service) -> None:
        self.service = service
        self.elapsed_total_seconds = None

    @abstractmethod
    def check(self, **kwargs) -> Tuple[bool, Optional[float]]:  # pragma: no cover
        pass


class SocketBackend(BaseBackend):
    def check(self) -> Tuple[bool, Optional[float]]:
        a_socket = socket(AF_INET, SOCK_STREAM)
        location = (self.service.domain, self.service.port)
        try:
            result_of_check = a_socket.connect_ex(location)
        except (error, timeout):
            return False, None
        else:
            a_socket.close()
        return result_of_check == 0, None


class RequestBackend(BaseBackend):
    def _get_url(self) -> str:
        protocol = 'https' if self.service.port == 443 else 'http'
        return f'{protocol}://{self.service.domain}:{self.service.port}'

    def check(self) -> Tuple[bool, Optional[float]]:
        url = self._get_url()
        try:
            response = requests.get(url)
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError):
            logger.warning(f'"{url}" request failed')
            return False, None
        else:
            elapsed_total_seconds = response.elapsed.total_seconds()
            return not (500 <= response.status_code <= 511), elapsed_total_seconds
