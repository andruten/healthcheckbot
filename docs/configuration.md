# Configuration

The application is configured through environment variables. In production (Docker), these are set in `docker-compose.yml`. For local development, use a `.env` file.

## Reference

| Variable             | Default         | Required | Description                              |
|----------------------|-----------------|----------|------------------------------------------|
| `TELEGRAM_BOT_TOKEN` | —               | Yes      | Token from BotFather                     |
| `DB_HOST`            | `localhost`     | No       | MySQL server hostname                    |
| `DB_PORT`            | `3306`          | No       | MySQL server port                        |
| `DB_USER`            | `healthchecker` | No       | MySQL user                               |
| `DB_PASSWORD`        | `healthchecker` | No       | MySQL password                           |
| `DB_NAME`            | `healthchecker` | No       | MySQL database name                      |
| `CHECK_INTERVAL_SEC` | `60`            | No       | Interval between check cycles (seconds)  |
| `DEFAULT_ALERT_DAYS` | `7`             | No       | Default days before SSL expiry to alert  |
| `RETENTION_DAYS`     | `7`             | No       | Days of raw health_checks kept before consolidation and purge |
| `LOG_LEVEL`          | `INFO`          | No       | Python log level (DEBUG, INFO, WARNING)  |

## Telegram Bot Token

To get a token:

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Copy the token and set it as `TELEGRAM_BOT_TOKEN`

## Database

MySQL is configured via `docker-compose.yml` with:
- User: `healthchecker`
- Password: `healthchecker`
- Database: `healthchecker`
- Port: `3307` (host) → `3306` (container)

To change credentials, update both `docker-compose.yml` and `.env`.

## Migrations (Aerich)

Tortoise ORM migrations are managed with Aerich. The config is in `src/healthchecker/infrastructure/persistence/tortoise_config.py`. After changing ORM models:

```bash
docker compose exec app aerich migrate
docker compose exec app aerich upgrade
```

## Per-URL Alert Configuration

When adding a URL via Telegram, you can override the default alert threshold:

```
/add https://example.com Example --alert-days 14
```

This sets a 14-day SSL expiry warning for that specific URL instead of the default 30 days.
