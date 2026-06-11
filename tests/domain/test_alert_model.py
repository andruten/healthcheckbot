from datetime import datetime, timezone

from healthchecker.domain.models.alert import Alert, AlertType


class TestAlertType:
    def test_ssl_expiry_value(self):
        assert AlertType.SSL_EXPIRY.value == "ssl_expiry"

    def test_http_down_value(self):
        assert AlertType.HTTP_DOWN.value == "http_down"


class TestAlertModel:
    def test_create_alert(self):
        now = datetime.now(timezone.utc)
        alert = Alert(
            id=None,
            url_id=1,
            alert_type=AlertType.SSL_EXPIRY,
            message="Certificate expires in 10 days",
            is_sent=False,
            created_at=now,
        )
        assert alert.id is None
        assert alert.url_id == 1
        assert alert.alert_type == AlertType.SSL_EXPIRY
        assert alert.message == "Certificate expires in 10 days"
        assert alert.is_sent is False
        assert alert.created_at == now

    def test_alert_with_id(self):
        now = datetime.now(timezone.utc)
        alert = Alert(
            id=5,
            url_id=2,
            alert_type=AlertType.HTTP_DOWN,
            message="Service is down",
            is_sent=True,
            created_at=now,
        )
        assert alert.id == 5
        assert alert.is_sent is True

    def test_mark_as_sent_mutation(self):
        now = datetime.now(timezone.utc)
        alert = Alert(
            id=1,
            url_id=1,
            alert_type=AlertType.SSL_EXPIRY,
            message="Test",
            is_sent=False,
            created_at=now,
        )
        alert.is_sent = True
        assert alert.is_sent is True
