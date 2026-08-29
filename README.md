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
| `DEGRADATION_ENABLED` | `true` | Enable early degradation detection |
| `DEGRADATION_WINDOW_SIZE` | `20` | Checks in the rolling window used as baseline |
| `DEGRADATION_TREND_SIZE` | `5` | Most recent checks compared against the baseline |
| `DEGRADATION_MIN_CHECKS` | `10` | Minimum checks before detection is meaningful |
| `DEGRADATION_MIN_TTFB_SAMPLES` | `5` | Minimum healthy TTFB samples to compute a baseline |
| `TTFB_DEGRADATION_MULTIPLIER` | `1.5` | TTFB degradation factor vs baseline median |
| `TTFB_WARN_FLOOR_MS` | `1000` | Minimum TTFB (ms) to consider degradation |
| `DEGRADATION_FAILURE_RATIO` | `0.5` | Max failure ratio treated as intermittent (above = down) |
| `DEGRADATION_MIN_FAILURES` | `3` | Minimum failures in window to flag intermittent degradation |

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
make up_build
```

This starts MySQL and the application. The bot starts receiving commands and running periodic checks.

## Makefile

All common tasks are automated via `make` and run through `docker compose`:

| Target | Description |
|---|---|
| `make up_build` | Start everything detached (build images first) |
| `make up` | Start detached (no rebuild) |
| `make run` | Start attached (with build) |
| `make down` | Stop everything |
| `make restart` | Restart the app |
| `make build` | Build production images |
| `make logs` | Follow app logs |
| `make ps` | List running services |
| `make bash` | Shell into the dev container |
| `make migrate` | Generate Aerich migration (needs app running) |
| `make upgrade` | Apply Aerich migration (needs app running) |
| `make mysql` | Open a MySQL client into the db container |
| `make test` | Run tests in the dev container |
| `make lint` | `ruff check --fix` in the dev container |
| `make lint_check` | `ruff check` (no fixes) |
| `make format` | `ruff format` |
| `make format_check` | `ruff format --check` |

Targets that need `.env` create it from `.env.example` automatically.

## Local development

No local Python required: tests, lint and format run in the `dev` compose service (profile `dev`), which builds the `dev` Docker stage with `.[dev]` installed and mounts `src/`, `tests/` and `pyproject.toml` from the host.

```bash
make test
make lint
make bash
```

## Migrations

```bash
make migrate     # Generate migration (needs app running)
make upgrade     # Apply migration (needs app running)
```
