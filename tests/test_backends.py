import unittest
from socket import error, timeout
from unittest.mock import MagicMock, patch

import requests

from backends import RequestBackend, SocketBackend


@patch('backends.socket')
class TestSocketBackend(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        service = MagicMock(domain='fake', port=456)
        self.backend = SocketBackend(service)

    def test_success(self, mock_socket):
        mock_socket.return_value.connect_ex.return_value = 0

        self.assertTrue(self.backend.check())

    def test_error(self, mock_socket):
        mock_socket.return_value.connect_ex.return_value = 1

        self.assertFalse(self.backend.check())

    def test_error_exception(self, mock_socket):
        mock_socket.return_value.connect_ex.side_effect = error

        self.assertFalse(self.backend.check())

    def test_timeout_exception(self, mock_socket):
        mock_socket.return_value.connect_ex.side_effect = timeout

        self.assertFalse(self.backend.check())


@patch('backends.requests.get')
class TestRequestBackend(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        service = MagicMock(domain='fake', port=80)
        self.backend = RequestBackend(service)

    def test_500(self, mock_head):
        mock_head.return_value = MagicMock(status_code=500)

        self.assertFalse(self.backend.check())

    def test_200(self, mock_head):
        mock_head.return_value = MagicMock(status_code=200)

        self.assertTrue(self.backend.check())

    def test_400(self, mock_head):
        mock_head.return_value = MagicMock(status_code=400)

        self.assertTrue(self.backend.check())

    def test_300(self, mock_head):
        mock_head.return_value = MagicMock(status_code=300)

        self.assertTrue(self.backend.check())

    def test_999(self, mock_head):
        mock_head.return_value = MagicMock(status_code=999)

        self.assertTrue(self.backend.check())

    def test_request_exception(self, mock_head):
        mock_head.side_effect = requests.exceptions.RequestException

        self.assertFalse(self.backend.check())
