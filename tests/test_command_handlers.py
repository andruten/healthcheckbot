import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from command_handlers import (add_service_command_handler, chat_service_checker_command_handler,
                              chat_services_checker_command_handler,
                              list_services_command_handler, remove_services_command_handler)
from models import Service, ServiceStatus


def mock_chat_handler_side_effect(*args, **kwargs):
    if args[0] == '1234':
        return {'1234': []}
    elif args[0] == '5678':
        return {'5678': []}


class TestCommandHandlers(unittest.TestCase):

    @patch('command_handlers.LocalJsonRepository.create')
    @patch('command_handlers.ServiceManager.fetch_active')
    def test_chat_service_checker_command_handler(
            self,
            mock_service_manager,
            mock_repository_create,
    ):
        mock_repository_create.return_value = MagicMock()
        with patch.object(Service, 'healthcheck_backend', new_callable=PropertyMock) as mock_healthcheck_backend:
            mock_ht_service = MagicMock(return_value=True)
            mock_healthcheck_backend.return_value = MagicMock(check=mock_ht_service)
            mock_service_manager.return_value = [
                Service(
                    service_type='request',
                    name='test',
                    domain='test.com',
                    port=443,
                    status=ServiceStatus.HEALTHY,
                ),
                Service(
                    service_type='request',
                    name='test2',
                    domain='test2.com',
                    port=443,
                    status=ServiceStatus.UNHEALTHY,
                ),
                Service(
                    service_type='socket',
                    name='test3',
                    domain='test3',
                    port=4442,
                    status=ServiceStatus.UNKNOWN,
                ),
            ]

            chat_services = chat_service_checker_command_handler('1234')

        self.assertIsInstance(chat_services, dict)
        self.assertTrue(len(chat_services), 1)

    @patch('command_handlers.LocalJsonRepository.create')
    @patch('command_handlers.ServiceManager.fetch_active')
    def test_chat_service_checker_command_handler_empty(
            self,
            mock_service_manager,
            mock_repository_create,
    ):
        mock_repository_create.return_value = MagicMock()
        with patch.object(Service, 'healthcheck_backend', new_callable=PropertyMock) as mock_healthcheck_backend:
            mock_ht_service = MagicMock(return_value=True)
            mock_healthcheck_backend.return_value = MagicMock(check=mock_ht_service)
            mock_service_manager.return_value = []

            chat_services = chat_service_checker_command_handler('1234')

        self.assertIsInstance(chat_services, dict)
        self.assertEqual(len(chat_services), 0)

    @patch('command_handlers.LocalJsonRepository.create')
    @patch('command_handlers.ServiceManager.fetch_active')
    def test_chat_service_checker_command_handler_unhealthy(
            self,
            mock_service_manager,
            mock_repository_create,
    ):
        mock_repository_create.return_value = MagicMock()
        with patch.object(Service, 'healthcheck_backend', new_callable=PropertyMock) as mock_healthcheck_backend:
            mock_ht_service = MagicMock(return_value=False)
            mock_healthcheck_backend.return_value = MagicMock(check=mock_ht_service)
            mock_service_manager.return_value = [
                Service(
                    service_type='request',
                    name='test',
                    domain='test.com',
                    port=443,
                    status=ServiceStatus.HEALTHY,
                ),
            ]

            chat_services = chat_service_checker_command_handler('1234')

        self.assertIsInstance(chat_services, dict)
        self.assertTrue(len(chat_services), 1)

    @patch('command_handlers.LocalJsonRepository.get_all_chat_ids')
    @patch('command_handlers.chat_service_checker_command_handler')
    def test_chat_services_checker_command_handler(self, mock_chat_handler, mock_chat_ids):
        mock_chat_handler.side_effect = mock_chat_handler_side_effect
        mock_chat_ids.return_value = ['1234', '5678']

        chat_failing_services = chat_services_checker_command_handler()

        self.assertIsInstance(chat_failing_services, dict)
        self.assertTrue(len(chat_failing_services), 2)

    @patch('command_handlers.LocalJsonRepository.create')
    @patch('command_handlers.ServiceManager.add')
    def test_add_service_command_handler(self, mock_service_manager_add, mock_repository_create):
        mock_service_manager_add.return_value = Service('request', 'test', 'test.com', 443)
        mock_repository_create.return_value = MagicMock()

        service = add_service_command_handler('1234', 'request', 'test', 'test.com', 443)

        self.assertIsInstance(service, Service)
        mock_service_manager_add.assert_called_once()
        mock_repository_create.assert_called_once()

    @patch('command_handlers.ServiceManager.remove')
    @patch('command_handlers.LocalJsonRepository.create')
    def test_remove_services_command_handler(self, mock_service_manager_remove, mock_repository_create):
        mock_service_manager_remove.return_value = True
        mock_repository_create.return_value = MagicMock()

        remove_services_command_handler('test', '1234')

        mock_service_manager_remove.assert_called_once()
        mock_repository_create.assert_called_once()

    @patch('command_handlers.LocalJsonRepository.create')
    @patch('command_handlers.ServiceManager.fetch_all')
    def test_list_services_command_handler(self, mock_fetch_all, mock_repository_create):
        mock_fetch_all.return_value = [
            Service(service_type='request', name='test', domain='test.com', port=443, status=ServiceStatus.HEALTHY),
            Service(service_type='request', name='test2', domain='test2.com', port=443, status=ServiceStatus.UNHEALTHY),
            Service(service_type='socket', name='test3', domain='test3', port=4442, status=ServiceStatus.UNKNOWN),
        ]
        mock_repository_create.return_value = MagicMock()
        services = list_services_command_handler('1234')

        self.assertIsInstance(services, list)
        self.assertTrue(len(services), 3)
