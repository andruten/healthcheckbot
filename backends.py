from abc import ABC, abstractmethod
import requests
import socket


class BaseBackend(ABC):

    def __init__(self, service) -> None:
        self.service = service

    @abstractmethod
    def check(self, **kwargs):
        pass


class SocketBackend(BaseBackend):

    def check(self):
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        location = (self.service.domain, self.service.port)
        try:
            result_of_check = a_socket.connect_ex(location)
        except socket.error:
            return False
        return bool(result_of_check == 0)


class RequestBackend(BaseBackend):

    def _get_url(self):
        protocol = 'https' if self.service.port == 443 else 'http'
        return f'{protocol}://{self.service.domain}:{self.service.port}'

    def check(self, timeout=5):
        url = self._get_url()
        try:
            response = requests.head(url, timeout=timeout)
        except requests.exceptions.RequestException:
            return False
        else:
            if response.status_code >= 400:
                return False
        return True
