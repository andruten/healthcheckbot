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
│   │   └── handlers/     # /start, /add, /list, /delete, /check, /results
│   └── scheduler.py
├── application/          # Use cases
│   ├── manage_urls.py
│   ├── get_results.py
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

```bash
docker compose up --build                  # Start everything
docker compose exec app aerich migrate     # Generate migration
docker compose exec app aerich upgrade     # Apply migration
PYTHONPATH=src python -m pytest tests/     # Run tests locally
```

## Tests

64 tests (53 unit + 11 integration with SQLite in-memory).

```
tests/
├── domain/           → models and services
├── application/      → use cases (mocking repos)
├── infrastructure/   → checkers, config, tortoise repos
└── interfaces/       → scheduler
```

## Update Rule
When adding a new global convention document under docs/, update this index in the same change.
