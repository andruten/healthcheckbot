# Tortoise ORM Migration

Replaced raw SQL (aiomysql) with Tortoise ORM + Aerich for database access.

## Changes

- Added Tortoise ORM models: `UrlModel`, `HealthCheckModel`, `AlertModel`, `DailySummaryModel`
- Replaced all four repository implementations with Tortoise-based versions
- Added `connect_database()` / `close_database()` with `Tortoise.init()` / `generate_schemas()`
- Removed raw SQL schema files and direct aiomysql usage
- Added `aiomysql` dependency (MySQL driver for Tortoise)
- Added Aerich integration for incremental migrations

## Why

- Async-native ORM (no thread pool for DB calls)
- Less boilerplate than raw SQL
- Standard migration workflow with Aerich
- Backend-agnostic: works with SQLite (tests) and MySQL (production)

## Notes

- Domain models remain separate from ORM models (DDD purity)
- Tests use SQLite in-memory via Tortoise
- `generate_schemas()` creates tables on startup (dev); migrate to `aerich upgrade` for production
