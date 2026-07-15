import asyncio

import pytest

from healthchecker.interfaces.scheduler import Scheduler


class TestScheduler:
    @pytest.fixture
    def mock_use_case(self, mocker):
        uc = mocker.AsyncMock()
        uc.execute.return_value = []
        return uc

    async def test_start_stop(self, mock_use_case, mocker):
        mocker.patch(
            "healthchecker.interfaces.scheduler.settings.check_interval_sec", 0.01
        )
        scheduler = Scheduler(mock_use_case)
        assert scheduler._running is False

        async def run():
            task = asyncio.create_task(scheduler.start())
            await asyncio.sleep(0.1)
            await scheduler.stop()
            await task

        await run()
        mock_use_case.execute.assert_awaited()

    async def test_start_with_alerts(self, mock_use_case, mocker):
        mocker.patch(
            "healthchecker.interfaces.scheduler.settings.check_interval_sec", 0.01
        )
        alert = mocker.Mock()
        alert.message = "Test alert"
        alert.id = 1
        mock_use_case.execute.return_value = [alert]

        alert_repo = mocker.AsyncMock()
        send_alert = mocker.AsyncMock()
        scheduler = Scheduler(
            mock_use_case, alert_repo=alert_repo, send_alert=send_alert
        )

        async def run():
            task = asyncio.create_task(scheduler.start())
            await asyncio.sleep(0.1)
            await scheduler.stop()
            await task

        await run()
        assert mock_use_case.execute.await_count >= 1
        send_alert.assert_awaited_with("Test alert")
        alert_repo.mark_as_sent.assert_awaited_with(1)

    async def test_dispatch_alerts_does_not_mark_failed_send_as_sent(self, mocker):
        alert = mocker.Mock()
        alert.message = "Bad markdown"
        alert.id = 1
        alert_repo = mocker.AsyncMock()
        send_alert = mocker.AsyncMock(side_effect=RuntimeError("telegram failed"))
        scheduler = Scheduler(
            mocker.AsyncMock(), alert_repo=alert_repo, send_alert=send_alert
        )

        await scheduler._dispatch_alerts([alert])

        send_alert.assert_awaited_once_with("Bad markdown")
        alert_repo.mark_as_sent.assert_not_called()
