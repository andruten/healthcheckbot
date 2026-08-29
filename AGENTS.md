# Health Checker

DDD project in Python that periodically monitors HTTP endpoints, measures TTFB and SSL expiration, and exposes results through a Telegram bot.

## Stack

- **Python 3.14** with strict typing
- **Tortoise ORM + Aerich** (MySQL 8, SQLite for tests)
- **python-telegram-bot** (async)
- **httpx** (async HTTP client)
- **cryptography** (SSL inspection)
- **Docker + docker-compose**
- **pytest + respx + pytest-mock** (tests)

## Architecture (DDD)

```
src/healthchecker/
├── interfaces/           # Telegram bot, asyncio scheduler
│   ├── telegram/
│   │   ├── bot.py
│   │   └── handlers/     # /start, /add, /list, /delete, /check, /stats
│   └── scheduler.py
├── application/          # Use cases
│   ├── manage_urls.py
│   ├── get_stats.py
│   ├── check_all_urls.py
│   └── consolidate_summaries.py
├── domain/               # Models, services, repository interfaces
│   ├── models/           # Url, HealthCheck, Alert, DailySummary
│   ├── services/         # HealthCheckService
│   └── repositories/     # Interfaces (Url, HealthCheck, Alert, DailySummary)
├── infrastructure/       # Persistence, checkers, config
│   ├── persistence/      # Tortoise ORM repos, tortoise_models, tortoise_config
│   ├── checker/          # HttpHealthChecker, SslChecker
│   └── config.py
└── main.py
```

## Useful commands

All tasks are automated via `make` (see `Makefile`). Everything runs through `docker compose`; dev commands (`test`, `lint`, `format`, `bash`) use the `dev` service (profile `dev`, built from the `dev` Docker stage with `.[dev]` installed).

```bash
make up_build           # Start everything (build images, detached)
make up                 # Start detached (no rebuild)
make run                # Start attached (with build)
make down               # Stop everything
make restart            # Restart the app
make build              # Build production images
make logs               # Follow app logs
make ps                 # List running services
make bash               # Shell into a dev container
make migrate            # Generate Aerich migration (needs app running)
make upgrade            # Apply Aerich migration (needs app running)
make mysql              # MySQL client into the db container
make test               # Run tests in the dev container
make lint               # ruff check --fix in the dev container
make lint_check         # ruff check (no fixes)
make format             # ruff format
make format_check       # ruff format --check
```

All targets that need `.env` create it from `.env.example` automatically (`check_env`).

## Tests

135 tests (unit + integration with SQLite in-memory).

```
tests/
├── domain/           → models and services
├── application/      → use cases (mocking repos)
├── infrastructure/   → checkers, config, tortoise repos
└── interfaces/       → scheduler
```

## Update Rule
When adding a new global convention document under docs/, update this index in the same change.
