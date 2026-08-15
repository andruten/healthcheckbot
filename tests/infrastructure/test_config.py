from healthchecker.infrastructure.config import Settings


class TestSettings:
    def test_default_values(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_PORT", raising=False)
        s = Settings()
        assert s.telegram_bot_token == ""
        assert s.db_host == "localhost"
        assert s.db_port == 3306
        assert s.db_user == "healthchecker"
        assert s.db_password == "healthchecker"
        assert s.db_name == "healthchecker"
        assert s.check_interval_sec == 60
        assert s.default_alert_days == 7
        assert s.log_level == "INFO"
        assert s.degradation_enabled is True
        assert s.degradation_window_size == 20
        assert s.degradation_trend_size == 5
        assert s.degradation_min_checks == 10
        assert s.degradation_min_ttfb_samples == 5
        assert s.ttfb_degradation_multiplier == 1.5
        assert s.ttfb_warn_floor_ms == 1000.0
        assert s.degradation_failure_ratio == 0.5
        assert s.degradation_min_failures == 3

    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("DB_HOST", "myhost")
        monkeypatch.setenv("DB_PORT", "3307")
        monkeypatch.setenv("DB_USER", "admin")
        monkeypatch.setenv("DB_PASSWORD", "secret")
        monkeypatch.setenv("DB_NAME", "mydb")
        monkeypatch.setenv("CHECK_INTERVAL_SEC", "120")
        monkeypatch.setenv("DEFAULT_ALERT_DAYS", "14")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DEGRADATION_ENABLED", "false")
        monkeypatch.setenv("DEGRADATION_WINDOW_SIZE", "40")
        monkeypatch.setenv("DEGRADATION_TREND_SIZE", "8")
        monkeypatch.setenv("DEGRADATION_MIN_CHECKS", "15")
        monkeypatch.setenv("DEGRADATION_MIN_TTFB_SAMPLES", "7")
        monkeypatch.setenv("TTFB_DEGRADATION_MULTIPLIER", "2.0")
        monkeypatch.setenv("TTFB_WARN_FLOOR_MS", "1500")
        monkeypatch.setenv("DEGRADATION_FAILURE_RATIO", "0.3")
        monkeypatch.setenv("DEGRADATION_MIN_FAILURES", "5")

        s = Settings()
        assert s.telegram_bot_token == "test_token"
        assert s.db_host == "myhost"
        assert s.db_port == 3307
        assert s.db_user == "admin"
        assert s.db_password == "secret"
        assert s.db_name == "mydb"
        assert s.check_interval_sec == 120
        assert s.default_alert_days == 14
        assert s.log_level == "DEBUG"
        assert s.degradation_enabled is False
        assert s.degradation_window_size == 40
        assert s.degradation_trend_size == 8
        assert s.degradation_min_checks == 15
        assert s.degradation_min_ttfb_samples == 7
        assert s.ttfb_degradation_multiplier == 2.0
        assert s.ttfb_warn_floor_ms == 1500.0
        assert s.degradation_failure_ratio == 0.3
        assert s.degradation_min_failures == 5

    def test_allowed_chat_ids_default_empty(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_CHAT_IDS", raising=False)
        s = Settings()
        assert s.allowed_chat_ids == frozenset()

    def test_allowed_chat_ids_single(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_CHAT_IDS", "12345678")
        s = Settings()
        assert s.allowed_chat_ids == frozenset({12345678})

    def test_allowed_chat_ids_multiple(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_CHAT_IDS", "12345678,87654321,11223344")
        s = Settings()
        assert s.allowed_chat_ids == frozenset({12345678, 87654321, 11223344})

    def test_allowed_chat_ids_with_spaces(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_CHAT_IDS", " 12345678 , 87654321 ")
        s = Settings()
        assert s.allowed_chat_ids == frozenset({12345678, 87654321})

    def test_allowed_chat_ids_empty_string(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_CHAT_IDS", "")
        s = Settings()
        assert s.allowed_chat_ids == frozenset()
