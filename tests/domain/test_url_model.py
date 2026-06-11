from healthchecker.domain.models.url import Url


class TestUrlModel:
    def test_create_url_with_defaults(self):
        url = Url.create("https://example.com")
        assert url.url == "https://example.com"
        assert url.name == "https://example.com"
        assert url.alert_before_days == 30
        assert url.is_active is True
        assert url.id is None

    def test_create_url_with_custom_name(self):
        url = Url.create("https://example.com", name="Example", alert_before_days=14)
        assert url.name == "Example"
        assert url.alert_before_days == 14

    def test_create_url_sets_timestamps(self):
        url = Url.create("https://example.com")
        assert url.created_at is not None
        assert url.updated_at is not None
