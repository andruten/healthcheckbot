import unittest
from unittest.mock import MagicMock

from models import ServiceStatus, Service
from repositories import ServiceRepository


class TestServices(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        mock_persistence_backend = MagicMock()
        self.service_manager = ServiceRepository(mock_persistence_backend)

    def test_mark_as_healthy(self):
        mock_service = MagicMock()
        self.service_manager.mark_as_healthy(mock_service)
        self.assertEqual(mock_service.status, ServiceStatus.HEALTHY)

    def test_mark_as_unhealthy(self):
        mock_service = MagicMock()
        self.service_manager.mark_as_unhealthy(mock_service)
        self.assertEqual(mock_service.status, ServiceStatus.UNHEALTHY)

    def test_fetch_all(self):
        self.service_manager.persistence_backend.fetch_all.return_value = [
            {"name": "test1", "url": "test1.com", "status": "unknown"},
            {"name": "test2", "url": "test2.com", "status": "healthy"},
            {"name": "test3", "url": "test3.com", "status": "unhealthy"},
        ]
        services = self.service_manager.fetch_all()
        self.assertTrue(all([isinstance(service, Service) for service in services]))

    def test_fetch_active(self):
        self.service_manager.persistence_backend.fetch_all.return_value = [
            {"name": "test1", "url": "test1.com", "status": "unknown"},
            {"name": "test2", "url": "test2.com", "status": "healthy"},
            {"name": "test3", "url": "test3.com", "status": "unhealthy"},
        ]
        services = self.service_manager.fetch_active()
        self.assertTrue(all([isinstance(service, Service) and service.enabled is True for service in services]))

    def test_add(self):
        self.service_manager.add('test', 'test.com')

    def test_remove(self):
        self.service_manager.remove('test1')
