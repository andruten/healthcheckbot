import pytest

from healthchecker.interfaces.telegram.bot import TelegramBot


class TestTelegramBot:
    async def test_send_alert_raises_after_send_failure(self, mocker):
        bot = TelegramBot(
            manage_urls=mocker.AsyncMock(),
            get_results=mocker.AsyncMock(),
            check_all_urls=mocker.AsyncMock(),
        )
        telegram_bot = mocker.Mock()
        telegram_bot.send_message = mocker.AsyncMock(side_effect=RuntimeError("bad"))
        bot._app = mocker.Mock(bot=telegram_bot)
        mocker.patch(
            "healthchecker.interfaces.telegram.bot.settings.allowed_chat_ids",
            {123, 456},
        )

        with pytest.raises(RuntimeError, match="Failed to send alert"):
            await bot.send_alert("Bad markdown")

        assert telegram_bot.send_message.await_count == 2
