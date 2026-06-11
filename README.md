# Health Checker

Periodic monitoring of HTTP endpoints. Measures **status code**, **TTFB** (Time To First Byte), and **SSL certificate expiration**. Results are queried through a Telegram bot.

## Stack

- Python 3.14 + asyncio
- Tortoise ORM + MySQL 8
- `httpx` (HTTP checks), `cryptography` (SSL)
- `python-telegram-bot`
- Docker + docker-compose
- pytest + respx + pytest-mock

## Configuration

Copy `.env.example` to `.env` and set the variables:

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token (from BotFather) |
| `ALLOWED_CHAT_IDS` | (empty) | Comma-separated authorized chat IDs. Empty = any chat |
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_USER` | `healthchecker` | MySQL user |
| `DB_PASSWORD` | `healthchecker` | MySQL password |
| `DB_NAME` | `healthchecker` | Database name |
| `CHECK_INTERVAL_SEC` | `60` | Interval between check cycles (seconds) |
| `DEFAULT_ALERT_DAYS` | `7` | SSL alert threshold in days |
| `RETENTION_DAYS` | `7` | Days to retain raw checks before purging |
| `LOG_LEVEL` | `INFO` | Log level |

## Bot commands

| Command | Description |
|---|---|
| `/help` | Show help with all commands |
| `/add <url> [name] [--alert-days N]` | Add a URL to monitor |
| `/list` | List monitored URLs with latest status |
| `/delete <id>` | Remove a URL by its ID |
| `/check` | Run checks immediately |
| `/results <id> [--limit N]` | Show check history for a URL |

## Quick start

```bash
docker compose up --build
```

This starts MySQL and the application. The bot starts receiving commands and running periodic checks.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
PYTHONPATH=src python -m pytest tests/
```

## Migrations

```bash
docker compose exec app aerich migrate     # Generate migration
docker compose exec app aerich upgrade     # Apply migration
```
