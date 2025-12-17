import unittest
from unittest.mock import MagicMock, patch

import httpx

from backends import RequestBackend


class TestRequestBackend(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        service = MagicMock(domain='fake', port=80)
        self.backend = RequestBackend(service)

    async def test_500(self):
        mock_session = MagicMock(status_code=500)

        response = await self.backend.check(mock_session)
        self.assertFalse(response.is_healthy)

    async def test_200(self):
        mock_session = MagicMock(status_code=200)

        response = await self.backend.check(mock_session)
        self.assertTrue(response.is_healthy)

    async def test_400(self):
        mock_session = MagicMock(status_code=400)

        response = await self.backend.check(mock_session)
        self.assertTrue(response.is_healthy)

    async def test_300(self):
        mock_session = MagicMock(status_code=300)

        response = await self.backend.check(mock_session)
        self.assertTrue(response.is_healthy)

    async def test_999(self):
        mock_session = MagicMock(status_code=999)

        response = await self.backend.check(mock_session)
        self.assertTrue(response.is_healthy)

    @patch('backends.logger')
    async def test_request_exception(self, mock_logger):
        mock_session = httpx.HTTPError

        response = await self.backend.check(mock_session)
        self.assertFalse(response.is_healthy)
        mock_logger.warning.assert_called_once()
