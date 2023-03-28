from abc import ABC, abstractmethod
from socket import AF_INET, SOCK_STREAM, error, socket, timeout

import requests


class BaseBackend(ABC):

    def __init__(self, service) -> None:
        self.service = service

    @abstractmethod
    def check(self, **kwargs):  # pragma: no cover
        pass


class SocketBackend(BaseBackend):

    def check(self):
        a_socket = socket(AF_INET, SOCK_STREAM)
        location = (self.service.domain, self.service.port)
        try:
            result_of_check = a_socket.connect_ex(location)
        except (error, timeout):
            return False
        return bool(result_of_check == 0)


class RequestBackend(BaseBackend):

    def _get_url(self):
        protocol = 'https' if self.service.port == 443 else 'http'
        return f'{protocol}://{self.service.domain}:{self.service.port}'

    def check(self, connection_timeout=5):
        url = self._get_url()
        try:
            response = requests.head(url, timeout=connection_timeout)
        except requests.exceptions.RequestException:
            return False
        else:
            if response.status_code >= 400:
                return False
        return True
