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
        mock_use_case.execute.return_value = ["alert1"]
        scheduler = Scheduler(mock_use_case)

        async def run():
            task = asyncio.create_task(scheduler.start())
            await asyncio.sleep(0.1)
            await scheduler.stop()
            await task

        await run()
        assert mock_use_case.execute.await_count >= 1
