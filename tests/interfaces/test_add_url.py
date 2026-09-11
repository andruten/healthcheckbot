from unittest.mock import AsyncMock, MagicMock

import pytest

from healthchecker.interfaces.telegram.handlers.add_url import AddUrlHandler


class TestAddUrlHandlerValidation:
    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com",
            "http://example.com/path",
            "imaps://mail.example.com",
            "imaps://mail.example.com:1993",
            "pop3s://mail.example.com",
            "smtps://smtp.example.com",
            "ftps://ftp.example.com",
            "ldaps://ldap.example.com",
            "mail.example.com:993",
            "host.sub.example.com:443",
        ],
    )
    def test_valid_urls(self, url):
        assert AddUrlHandler._is_valid_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "not-a-url",
            "mail.example.com",
            "ftp://example.com",
            "imaps:/missing-slashes.com",
            "https://",
            "example.com:notaport",
            "example.com:99999",
            " ",
            "",
        ],
    )
    def test_invalid_urls(self, url):
        assert AddUrlHandler._is_valid_url(url) is False


class TestAddUrlHandler:
    @pytest.fixture
    def manage_urls(self):
        return AsyncMock()

    @pytest.fixture
    def update(self):
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def context(self):
        return MagicMock()

    async def test_add_imaps_url(self, manage_urls, update, context):
        context.args = ["imaps://mail.example.com", "MyMail"]
        handler = AddUrlHandler(manage_urls)

        await handler.handle(update, context)

        manage_urls.add.assert_awaited_once_with(
            url="imaps://mail.example.com", name="MyMail", alert_before_days=30
        )
        update.message.reply_text.assert_awaited_once()

    async def test_add_bare_host_port(self, manage_urls, update, context):
        context.args = ["mail.example.com:993"]
        handler = AddUrlHandler(manage_urls)

        await handler.handle(update, context)

        manage_urls.add.assert_awaited_once_with(
            url="mail.example.com:993", name=None, alert_before_days=30
        )
        update.message.reply_text.assert_awaited_once()

    async def test_add_invalid_url_replies_error(self, manage_urls, update, context):
        context.args = ["not-a-url"]
        handler = AddUrlHandler(manage_urls)

        await handler.handle(update, context)

        manage_urls.add.assert_not_awaited()
        update.message.reply_text.assert_awaited_once()
        assert "Invalid URL" in update.message.reply_text.call_args[0][0]

    async def test_add_without_args_shows_usage_with_tls_examples(
        self, manage_urls, update, context
    ):
        context.args = None
        handler = AddUrlHandler(manage_urls)

        await handler.handle(update, context)

        manage_urls.add.assert_not_awaited()
        text = update.message.reply_text.call_args[0][0]
        assert "imaps://mail.example.com" in text
        assert "mail.example.com:993" in text
