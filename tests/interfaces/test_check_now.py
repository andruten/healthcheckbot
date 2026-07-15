from healthchecker.interfaces.telegram.handlers.check_now import CheckNowHandler


class TestCheckNowHandler:
    async def test_dispatch_alerts_does_not_mark_failed_send_as_sent(self, mocker):
        alert = mocker.Mock()
        alert.message = "Bad markdown"
        alert.id = 1
        alert_repo = mocker.AsyncMock()
        send_alert = mocker.AsyncMock(side_effect=RuntimeError("telegram failed"))
        handler = CheckNowHandler(
            mocker.AsyncMock(), alert_repo=alert_repo, send_alert=send_alert
        )

        await handler._dispatch_alerts([alert])

        send_alert.assert_awaited_once_with("Bad markdown")
        alert_repo.mark_as_sent.assert_not_called()
