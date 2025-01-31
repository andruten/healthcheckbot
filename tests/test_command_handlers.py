import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from commands.handlers import (add_service_command_handler, chat_service_checker_command_handler,
                              chat_services_checker_command_handler,
                              list_services_command_handler, remove_services_command_handler)
from models import Service, ServiceStatus


def mock_chat_handler_side_effect(*args, **kwargs):
    if args[0] == '1234':
        return {'1234': []}
    elif args[0] == '5678':
        return {'5678': []}


class TestCommandHandlers(unittest.TestCase):

    @patch('commands.handlers.LocalJsonRepository.create')
    @patch('commands.handlers.ServiceRepository.fetch_active')
    async def test_chat_service_checker_command_handler(
            self,
            mock_service_manager,
            mock_repository_create,
    ):
        mock_repository_create.return_value = MagicMock()
        with patch.object(Service, 'healthcheck_backend', new_callable=PropertyMock) as mock_healthcheck_backend:
            mock_ht_service = MagicMock(return_value=(True, None))
            mock_healthcheck_backend.return_value = MagicMock(check=mock_ht_service)
            mock_service_manager.return_value = [
                Service(
                    name='test',
                    url='test.com',
                    status=ServiceStatus.HEALTHY,
                ),
                Service(
                    name='test2',
                    url='test2.com',
                    status=ServiceStatus.UNHEALTHY,
                ),
                Service(
                    name='test3',
                    url='test3',
                    status=ServiceStatus.UNKNOWN,
                ),
            ]

            chat_services = chat_service_checker_command_handler('1234')

        self.assertIsInstance(chat_services, dict)
        self.assertTrue(len(chat_services), 1)

    @patch('commands.handlers.LocalJsonRepository.create')
    @patch('commands.handlers.ServiceRepository.fetch_active')
    async def test_chat_service_checker_command_handler_empty(
            self,
            mock_service_manager,
            mock_repository_create,
    ):
        mock_repository_create.return_value = MagicMock()
        with patch.object(Service, 'healthcheck_backend', new_callable=PropertyMock) as mock_healthcheck_backend:
            mock_ht_service = MagicMock(return_value=(True, None))
            mock_healthcheck_backend.return_value = MagicMock(check=mock_ht_service)
            mock_service_manager.return_value = []

            chat_services = await chat_service_checker_command_handler('1234')

        self.assertIsInstance(chat_services, dict)
        self.assertEqual(len(chat_services), 0)

    @patch('commands.handlers.LocalJsonRepository.create')
    @patch('commands.handlers.ServiceRepository.fetch_active')
    async def test_chat_service_checker_command_handler_unhealthy(
            self,
            mock_service_manager,
            mock_repository_create,
    ):
        mock_repository_create.return_value = MagicMock()
        with patch.object(Service, 'healthcheck_backend', new_callable=PropertyMock) as mock_healthcheck_backend:
            mock_ht_service = MagicMock(return_value=(False, None))
            mock_healthcheck_backend.return_value = MagicMock(check=mock_ht_service)
            mock_service_manager.return_value = [
                Service(
                    name='test',
                    url='test.com',
                    status=ServiceStatus.HEALTHY,
                ),
            ]

            chat_services = await chat_service_checker_command_handler('1234')

        self.assertIsInstance(chat_services, dict)
        self.assertTrue(len(chat_services), 1)

    @patch('commands.handlers.LocalJsonRepository.get_all_chat_ids')
    @patch('commands.handlers.chat_service_checker_command_handler')
    async def test_chat_services_checker_command_handler(self, mock_chat_handler, mock_chat_ids):
        mock_chat_handler.side_effect = mock_chat_handler_side_effect
        mock_chat_ids.return_value = ['1234', '5678']

        chat_failing_services = await chat_services_checker_command_handler()

        self.assertIsInstance(chat_failing_services, dict)
        self.assertTrue(len(chat_failing_services), 2)

    @patch('commands.handlers.LocalJsonRepository.create')
    @patch('commands.handlers.ServiceRepository.add')
    def test_add_service_command_handler(self, mock_service_manager_add, mock_repository_create):
        mock_service_manager_add.return_value = Service('test', 'test.com')
        mock_repository_create.return_value = MagicMock()

        service = add_service_command_handler('1234', 'test', 'test.com')

        self.assertIsInstance(service, Service)
        mock_service_manager_add.assert_called_once()
        mock_repository_create.assert_called_once()

    @patch('commands.handlers.ServiceRepository.remove')
    @patch('commands.handlers.LocalJsonRepository.create')
    def test_remove_services_command_handler(self, mock_service_manager_remove, mock_repository_create):
        mock_service_manager_remove.return_value = True
        mock_repository_create.return_value = MagicMock()

        remove_services_command_handler('test', '1234')

        mock_service_manager_remove.assert_called_once()
        mock_repository_create.assert_called_once()

    @patch('commands.handlers.LocalJsonRepository.create')
    @patch('commands.handlers.ServiceRepository.fetch_all')
    def test_list_services_command_handler(self, mock_fetch_all, mock_repository_create):
        mock_fetch_all.return_value = [
            Service(name='test', url='test.com', status=ServiceStatus.HEALTHY),
            Service(name='test2', url='test2.com', status=ServiceStatus.UNHEALTHY),
            Service(name='test3', url='test3', status=ServiceStatus.UNKNOWN),
        ]
        mock_repository_create.return_value = MagicMock()
        services = list_services_command_handler('1234')

        self.assertIsInstance(services, str)
        self.assertTrue(len(services), 3)
