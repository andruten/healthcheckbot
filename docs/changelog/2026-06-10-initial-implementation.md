# Initial Implementation

**Date:** 2026-06-10

## Summary

Initial implementation of the Health Checker application following Domain-Driven Design.

## Architecture

- **Domain Layer**: `Url`, `HealthCheck`, `Alert` models with `HealthCheckService` domain service
- **Application Layer**: Use cases for managing URLs, checking all URLs, and querying results
- **Infrastructure Layer**: MySQL persistence (aiomysql), HTTP checker (httpx), SSL checker (cryptography)
- **Interfaces Layer**: Telegram bot (python-telegram-bot), asyncio-based scheduler

## Files Created

### Documentation
- `docs/index.md` — Project overview
- `docs/architecture.md` — Layered architecture description
- `docs/ddd-model.md` — Domain model with entities, value objects, and repositories
- `docs/setup.md` — Setup guide for Docker and local development
- `docs/configuration.md` — Environment variable reference
- `docs/telegram-commands.md` — Bot command reference

### Code
- `src/healthchecker/main.py` — Entry point with dependency wiring
- `src/healthchecker/domain/models/url.py` — Url entity
- `src/healthchecker/domain/models/health_check.py` — HealthCheck value object
- `src/healthchecker/domain/models/alert.py` — Alert entity with AlertType enum
- `src/healthchecker/domain/services/health_check_service.py` — SSL/HTTP alert logic
- `src/healthchecker/domain/repositories/url_repository.py` — Url repository interface
- `src/healthchecker/domain/repositories/health_check_repository.py` — HealthCheck repository interface
- `src/healthchecker/domain/repositories/alert_repository.py` — Alert repository interface
- `src/healthchecker/application/use_cases/manage_urls.py` — CRUD use cases for URLs
- `src/healthchecker/application/use_cases/get_results.py` — Results query use cases
- `src/healthchecker/application/use_cases/check_all_urls.py` — Health check orchestration
- `src/healthchecker/infrastructure/config.py` — Environment-based configuration
- `src/healthchecker/infrastructure/persistence/database.py` — MySQL connection pool and schema
- `src/healthchecker/infrastructure/persistence/url_repository.py` — MySQL Url repository
- `src/healthchecker/infrastructure/persistence/health_check_repository.py` — MySQL HealthCheck repository
- `src/healthchecker/infrastructure/persistence/alert_repository.py` — MySQL Alert repository
- `src/healthchecker/infrastructure/checker/http_checker.py` — HTTP health checker (httpx)
- `src/healthchecker/infrastructure/checker/ssl_checker.py` — SSL certificate checker
- `src/healthchecker/interfaces/telegram/bot.py` — Telegram bot setup and command routing
- `src/healthchecker/interfaces/telegram/handlers/add_url.py` — /add command handler
- `src/healthchecker/interfaces/telegram/handlers/list_urls.py` — /list command handler
- `src/healthchecker/interfaces/telegram/handlers/delete_url.py` — /delete command handler
- `src/healthchecker/interfaces/telegram/handlers/check_now.py` — /check command handler
- `src/healthchecker/interfaces/telegram/handlers/results.py` — /results command handler
- `src/healthchecker/interfaces/scheduler.py` — Periodic health check scheduler

### Infrastructure
- `Dockerfile` — Python 3.14 slim container
- `docker-compose.yml` — App + MySQL 8 services
- `pyproject.toml` — Package configuration
- `requirements.txt` — Python dependencies
- `.env.example` — Environment variable template

### Tests
- `tests/domain/test_health_check_service.py` — Domain service unit tests
- `tests/domain/test_url_model.py` — Url model unit tests
