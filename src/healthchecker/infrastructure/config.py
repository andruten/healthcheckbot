import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.db_host: str = os.getenv("DB_HOST", "localhost")
        self.db_port: int = int(os.getenv("DB_PORT", "3306"))
        self.db_user: str = os.getenv("DB_USER", "healthchecker")
        self.db_password: str = os.getenv("DB_PASSWORD", "healthchecker")
        self.db_name: str = os.getenv("DB_NAME", "healthchecker")
        self.check_interval_sec: int = int(os.getenv("CHECK_INTERVAL_SEC", "60"))
        self.default_alert_days: int = int(os.getenv("DEFAULT_ALERT_DAYS", "7"))
        self.retention_days: int = int(os.getenv("RETENTION_DAYS", "7"))
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.allowed_chat_ids: frozenset[int] = self._parse_chat_ids(
            os.getenv("ALLOWED_CHAT_IDS", "")
        )

    @staticmethod
    def _parse_chat_ids(raw: str) -> frozenset[int]:
        if not raw or not raw.strip():
            return frozenset()
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        return frozenset(int(p) for p in parts)


settings = Settings()
