import unittest
from unittest.mock import MagicMock

from models import ServiceManager, ServiceStatus, Service


class TestServices(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        mock_persistence_backend = MagicMock()
        self.service_manager = ServiceManager(mock_persistence_backend)

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
            {"service_type": "request", "name": "test1", "domain": "test1.com", "port": 443, "enabled": True,
             "status": "unknown"},
            {"service_type": "request", "name": "test2", "domain": "test2.com", "port": 443, "enabled": True,
             "status": "healthy"},
            {"service_type": "request", "name": "test3", "domain": "test3.com", "port": 443, "enabled": True,
             "status": "unhealthy"},
        ]
        services = self.service_manager.fetch_all()
        self.assertTrue(all([isinstance(service, Service) for service in services]))

    def test_fetch_active(self):
        self.service_manager.persistence_backend.fetch_all.return_value = [
            {"service_type": "request", "name": "test1", "domain": "test1.com", "port": 443, "enabled": True,
             "status": "unknown"},
            {"service_type": "request", "name": "test2", "domain": "test2.com", "port": 443, "enabled": True,
             "status": "healthy"},
            {"service_type": "request", "name": "test3", "domain": "test3.com", "port": 443, "enabled": False,
             "status": "unhealthy"},
        ]
        services = self.service_manager.fetch_active()
        self.assertTrue(all([isinstance(service, Service) and service.enabled is True for service in services]))

    def test_add(self):
        self.service_manager.add('request', 'test', 'test.com', 443)

    def test_remove(self):
        self.service_manager.remove('test1')
