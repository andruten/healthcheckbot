import unittest
from socket import error, timeout
from unittest.mock import MagicMock, patch

import httpx

from backends import RequestBackend, SocketBackend


@patch('backends.socket')
class TestSocketBackend(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        service = MagicMock(domain='fake', port=456)
        self.backend = SocketBackend(service)

    def test_success(self, mock_socket):
        mock_socket.return_value.connect_ex.return_value = 0

        is_healthy, time_to_first_byte, expire_date = self.backend.check()
        self.assertTrue(is_healthy)

    def test_error(self, mock_socket):
        mock_socket.return_value.connect_ex.return_value = 1

        is_healthy, time_to_first_byte, expire_date = self.backend.check()
        self.assertFalse(is_healthy)

    def test_error_exception(self, mock_socket):
        mock_socket.return_value.connect_ex.side_effect = error

        is_healthy, time_to_first_byte, expire_date = self.backend.check()
        self.assertFalse(is_healthy)

    def test_timeout_exception(self, mock_socket):
        mock_socket.return_value.connect_ex.side_effect = timeout

        is_healthy, time_to_first_byte, expire_date = self.backend.check()
        self.assertFalse(is_healthy)


class TestRequestBackend(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        service = MagicMock(domain='fake', port=80)
        self.backend = RequestBackend(service)

    async def test_500(self):
        mock_session = MagicMock(status_code=500)

        is_healthy, time_to_first_byte, expire_date = await self.backend.check(mock_session)
        self.assertFalse(is_healthy)

    async def test_200(self):
        mock_session = MagicMock(status_code=200)

        is_healthy, time_to_first_byte, expire_date = await self.backend.check(mock_session)
        self.assertTrue(is_healthy)

    async def test_400(self):
        mock_session = MagicMock(status_code=400)

        is_healthy, time_to_first_byte, expire_date = await self.backend.check(mock_session)
        self.assertTrue(is_healthy)

    async def test_300(self):
        mock_session = MagicMock(status_code=300)

        is_healthy, time_to_first_byte, expire_date = await self.backend.check(mock_session)
        self.assertTrue(is_healthy)

    async def test_999(self):
        mock_session = MagicMock(status_code=999)

        is_healthy, time_to_first_byte, expire_date = await self.backend.check(mock_session)
        self.assertTrue(is_healthy)

    @patch('backends.logger')
    async def test_request_exception(self, mock_logger):
        mock_session = httpx.HTTPError

        is_healthy, time_to_first_byte, expire_date = await self.backend.check(mock_session)
        self.assertFalse(is_healthy)
        mock_logger.warning.assert_called_once()
