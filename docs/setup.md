# Setup Guide

## Prerequisites

- Docker & Docker Compose
- Python 3.14+ (for local development)
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))

## Quick Start

### 1. Clone and configure

```bash
cp .env.example .env
```

Edit `.env` and fill in your Telegram bot token:

```
TELEGRAM_BOT_TOKEN=your_token_here
```

### 2. Run with Docker

```bash
docker-compose up --build
```

This starts:
- `healthchecker-db` — MySQL 8 instance on port 3307
- `healthchecker-app` — the Python application

The app uses Tortoise ORM and generates the database schema automatically on first run via `generate_schemas()`. For production schema changes, use Aerich migrations (see "Migrations").

### 3. Start using the bot

Open Telegram and find your bot. Send `/start`.

## Local Development

### 1. Create virtual environment

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start MySQL

```bash
docker-compose up db
```

### 4. Migrations (Aerich)

After changing Tortoise ORM models, generate and apply migrations:

```bash
# Generate a new migration
docker compose exec app aerich migrate

# Apply pending migrations
docker compose exec app aerich upgrade

# Check history
docker compose exec app aerich history
```

### 5. Run the application

```bash
python -m src.healthchecker.main
```

## Environment Variables

| Variable             | Default         | Description                        |
|----------------------|-----------------|------------------------------------|
| `TELEGRAM_BOT_TOKEN` | —               | Telegram bot token (required)      |
| `DB_HOST`            | `localhost`     | MySQL host                         |
| `DB_PORT`            | `3306`          | MySQL port                         |
| `DB_USER`            | `healthchecker` | MySQL user                         |
| `DB_PASSWORD`        | `healthchecker` | MySQL password                     |
| `DB_NAME`            | `healthchecker` | MySQL database name                |
| `CHECK_INTERVAL_SEC` | `60`            | Seconds between health check cycles |
| `DEFAULT_ALERT_DAYS` | `7`             | Default SSL expiry alert threshold  |
| `RETENTION_DAYS`     | `7`             | Days of raw health_checks kept before consolidation and purge |
| `LOG_LEVEL`          | `INFO`          | Logging level                      |
