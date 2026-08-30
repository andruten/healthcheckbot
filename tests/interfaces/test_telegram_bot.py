import logging

import pytest

from healthchecker.interfaces.telegram.bot import TelegramBot


class TestTelegramBotSendAlert:
    @pytest.fixture
    def telegram_bot(self, mocker):
        bot = TelegramBot(
            manage_urls=mocker.AsyncMock(),
            get_stats=mocker.AsyncMock(),
            check_all_urls=mocker.AsyncMock(),
        )
        app = mocker.MagicMock()
        app.bot.send_message = mocker.AsyncMock()
        app.updater.bot.get_updates = mocker.AsyncMock()
        bot._app = app
        return bot

    @staticmethod
    def _patch_chat_ids(mocker, chat_ids):
        mocker.patch(
            "healthchecker.interfaces.telegram.bot.settings.allowed_chat_ids",
            frozenset(chat_ids),
        )

    async def test_sends_to_each_allowed_chat(self, telegram_bot, mocker):
        self._patch_chat_ids(mocker, {111, 222})

        await telegram_bot.send_alert("Site is down")

        send_message = telegram_bot._app.bot.send_message
        assert send_message.await_count == 2
        chat_ids = {call.kwargs["chat_id"] for call in send_message.await_args_list}
        assert chat_ids == {"111", "222"}
        telegram_bot._app.updater.bot.get_updates.assert_not_awaited()

    async def test_continues_after_send_failure(self, telegram_bot, mocker):
        self._patch_chat_ids(mocker, {111, 222})
        send_message = telegram_bot._app.bot.send_message
        send_message.side_effect = [RuntimeError("boom"), None]

        await telegram_bot.send_alert("Site is down")

        assert send_message.await_count == 2

    async def test_empty_recipients_skip_send_and_warn_once(
        self, telegram_bot, mocker, caplog
    ):
        self._patch_chat_ids(mocker, set())

        with caplog.at_level(logging.WARNING):
            await telegram_bot.send_alert("down")
            await telegram_bot.send_alert("up")

        telegram_bot._app.bot.send_message.assert_not_awaited()
        telegram_bot._app.updater.bot.get_updates.assert_not_awaited()
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert "ALLOWED_CHAT_IDS" in warnings[0].getMessage()

    async def test_without_app_returns_early(self, mocker):
        bot = TelegramBot(
            manage_urls=mocker.AsyncMock(),
            get_stats=mocker.AsyncMock(),
            check_all_urls=mocker.AsyncMock(),
        )

        await bot.send_alert("down")
