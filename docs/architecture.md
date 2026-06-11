# Architecture

## Overview

Health Checker follows **Domain-Driven Design (DDD)** with a layered architecture. The application periodically monitors HTTP endpoints, measures performance, tracks SSL certificate expiration, and exposes results through a Telegram bot.

## Layers

```
┌─────────────────────────────────────────────┐
│               Interfaces                     │
│  (Telegram Bot, Scheduler, CLI)              │
├─────────────────────────────────────────────┤
│              Application                     │
│  (Use Cases: CheckAllUrls, ManageUrls, etc.) │
├─────────────────────────────────────────────┤
│               Domain                         │
│  (Models, Services, Repository Interfaces)   │
├─────────────────────────────────────────────┤
│            Infrastructure                    │
│  (Persistence, HTTP Checker, SSL Checker)    │
└─────────────────────────────────────────────┘
```

### Domain Layer
The core of the system. Contains:
- **Entities**: `Url`, `Alert` — objects with identity
- **Value Objects**: `HttpStatus`, `Ttfb`, `AlertConfig`, `UrlId` — immutable by value
- **Domain Services**: `HealthCheckService` — pure business logic
- **Repository Interfaces**: Contracts for persistence

### Application Layer
Orchestrates domain objects to fulfill use cases:
- `CheckAllUrlsUseCase` — runs health checks for all active URLs
- `ManageUrlsUseCase` — CRUD operations for monitored URLs
- `GetResultsUseCase` — queries health check history

### Infrastructure Layer
Implements the contracts defined by the domain:
- **Persistence**: MySQL via Tortoise ORM (aiomysql), repository implementations
- **Checkers**: HTTP client (httpx), SSL certificate inspection (cryptography)

### Interfaces Layer
Entry points for external actors:
- **Telegram Bot**: python-telegram-bot with command handlers
- **Scheduler**: asyncio-based loop that triggers checks every 60 seconds

## Data Flow

```
Scheduler (every 60s)
  │
  ▼
CheckAllUrlsUseCase
  │
  ├─▶ For each active Url ───────────────────────────┐
  │                                                   │
  ├─▶ HttpHealthChecker.check(url) ──▶ status + TTFB  │
  ├─▶ SslChecker.check(url)   ──────▶ expiration date │
  │                                                   │
  ▼                                                   ▼
HealthCheckService.evaluate(...) ──▶ HealthCheck + Alert[]
  │                                                   │
  ▼                                                   ▼
HealthCheckRepository.save(check)    AlertRepository.save(alert)
  │                                                   │
  ▼                                                   ▼
TelegramNotifier (if alert triggered)
```

## Technology Stack

| Component       | Technology              |
|-----------------|-------------------------|
| Language        | Python 3.14             |
| HTTP Client     | httpx (async)           |
| SSL             | cryptography            |
| Database        | MySQL 8                 |
| ORM             | Tortoise ORM + Aerich   |
| DB Driver       | aiomysql                |
| Telegram SDK    | python-telegram-bot     |
| Container       | Docker + docker-compose |
